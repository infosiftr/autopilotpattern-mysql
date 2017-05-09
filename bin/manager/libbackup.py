from datetime import datetime
import os
import shutil
import tempfile
from manager.libmanta import Manta

class BaseBackup(object):
    def __init__(self, consul, backup_id_fmt):
        self.consul = consul
        self.backup_id_fmt = backup_id_fmt
        self.workspace = None

    def _put_backup(self, infile, backup_id):
        raise NotImplementedError

    def _get_backup(self, backup_id, workspace):
        raise NotImplementedError

    def __make_workspace(self):
        if not self.workspace:
            self.workspace = tempfile.mkdtemp()

    def __clean_workspace(self):
        if self.workspace:
            shutil.rmtree(self.workspace)
            self.workspace = None

    def put_backup(self, backup_func):
        # TODO get lock
        # self.consul...
        # get any previous backup info from consul
        previous_data = self.consul.get_snapshot_data()

        # get time now so it is consistant throughout the backup process
        backup_time = datetime.utcnow()
        # backup_id generation from format string using time
        backup_id = now.strftime('{}'.format(self.backup_id_fmt))

        # make a working space that the db can use
        # we'll clean it up at the end
        workspace = self.__make_workspace()

        # have the db make a backup
        infile, extra_data = backup_func(workspace, backup_time, previous_data['extra'])

        if infile:
            self._put_backup(infile, backup_id)
            # TODO store backup info in consul

        # TODO release lock
        # self.consul...

        # clean up
        self.__clean_workspace(workspace)

    def get_backup(self, restore_func):
        current_data = self.consul.get_snapshot_data() or {}
        backup_id = current_data.get('id')
        datafile = None
        if backup_id:
            # make a space for backup storage to download the backup
            workspace = self.__make_workspace()
            # download the backup file
            datafile = self._get_backup(backup_id, workspace)

            # make a new space for db so that it can extract if needed
            db_workspace = self.__make_workspace()
            # have the db restore from the given file
            was_restored = restore_func(datafile, db_workspace)

            # clean up the workspaces
            self.__clean_workspace(db_workspace)
            self.__clean_workspace(workspace)

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

    def _put_backup(self, infile, backup_id):
        raise NotImplementedError

    def _get_backup(self, backup_id, workspace):
        raise NotImplementedError
