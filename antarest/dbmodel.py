# noinspection PyUnresolvedReferences
from antarest.core.configdata import model as configdatamodel

# noinspection PyUnresolvedReferences
from antarest.core.filetransfer import model as filetransfermodel

# noinspection PyUnresolvedReferences
from antarest.core.persistence import Base as PersistenceBase

# noinspection PyUnresolvedReferences
from antarest.core.tasks import model as tasksmodel

# noinspection PyUnresolvedReferences
from antarest.launcher import model as launchermodel

# noinspection PyUnresolvedReferences
from antarest.login import model as loginmodel

# noinspection PyUnresolvedReferences
from antarest.matrixstore import model as matrixstoremodel

# noinspection PyUnresolvedReferences
from antarest.study import model as studymodel

# noinspection PyUnresolvedReferences
from antarest.study.storage.variantstudy.model import dbmodel as variantmodel

Base = PersistenceBase
