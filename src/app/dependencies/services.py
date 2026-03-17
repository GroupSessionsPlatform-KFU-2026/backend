from typing import Annotated

from fastapi import Depends

from src.app.services.projects import ProjectService
from src.app.services.rooms import RoomService
from src.app.services.users import UserService

UserServiceDep = Annotated[UserService, Depends(UserService)]
ProjectServiceDep = Annotated[ProjectService, Depends(ProjectService)]
RoomServiceDep = Annotated[RoomService, Depends(RoomService)]
