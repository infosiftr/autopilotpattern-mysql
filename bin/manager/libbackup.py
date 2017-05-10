from datetime import datetime
import os
import shutil
import tempfile
from manager.libmanta import Manta
from manager.utils import debug

class BaseBackup(object):
    def __init__(self, consul, backup_id_fmt):
        self.consul = consul
        self.backup_id_fmt = backup_id_fmt

    def _put_backup(self, infile, backup_id):
        raise NotImplementedError

    def _get_backup(self, backup_id, workspace):
        raise NotImplementedError

    @debug
    def put_backup(self, node_name, backup_func):
        if not self.consul.lock_snapshot(node_name):
            log.info('Unable to grab snapshot lock.')
            return
        # get any previous backup info from consul
        previous_data = self.consul.get_snapshot_data()
        if previous_data is None or 'extra' not in previous_data:
            extra_data = None
        else:
            extra_data = previous_data['extra']

        # get time now so it is consistant throughout the backup process
        backup_time = datetime.utcnow()
        # backup_id generation from format string using time
        backup_id = backup_time.strftime('{}'.format(self.backup_id_fmt))

        # make a working space that the db can use
        # we'll clean it up at the end
        workspace = tempfile.mkdtemp()

        # have the db make a backup
        infile, extra_data_p = backup_func(workspace, backup_time, extra_data)

        if infile:
            self._put_backup(infile, backup_id)
            self.consul.record_snapshot_data({'id' : backup_id, 'extra' : extra_data_p})

        self.consul.unlock_snapshot()

        # clean up
        shutil.rmtree(workspace)

    @debug
    def get_backup(self, restore_func):
        current_data = self.consul.get_snapshot_data() or {}
        backup_id = current_data.get('id')
        datafile = None
        if backup_id:
            # make a space for backup storage to download the backup
            workspace = tempfile.mkdtemp()
            # download the backup file
            datafile = self._get_backup(backup_id, workspace)

            # make a new space for db so that it can extract if needed
            db_workspace = tempfile.mkdtemp()
            # have the db restore from the given file
            was_restored = restore_func(datafile, db_workspace)

            # clean up the workspaces
            shutil.rmtree(db_workspace)
            shutil.rmtree(workspace)

        return datafile is not None

class MantaBackup(BaseBackup):
    def __init__(self, consul, backup_id_fmt):
        BaseBackup.__init__(self, consul, backup_id_fmt)
        self.manta = Manta()

    def _put_backup(self, infile, backup_id):
        self.manta.put_backup(backup_id, infile)

    def _get_backup(self, backup_id, workspace):
        return manta.get_backup(backup_id, workspace)

class LocalBackup(BaseBackup):
    def __init__(self, consul, backup_id_fmt):
        BaseBackup.__init__(self, consul, backup_id_fmt)

    @debug
    def _put_backup(self, infile, backup_id):
        os.rename(infile, os.path.join('/tmp/backup', backup_id))

    @debug
    def _get_backup(self, backup_id, workspace):
        dstfile = os.path.join(workspace, backup_id)
        os.rename(os.path.join('/tmp/backup', backup_id), dstfile)
        return dstfile
