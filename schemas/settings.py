from pydantic import BaseModel

class SettingsBase(BaseModel):

    site_name:str

    support_email:str

    phone:str

    address:str

    theme:str

    primary_color:str

    language:str

    timezone:str

    allow_registration:bool

    maintenance_mode:bool

    live_provider:str


class SettingsResponse(SettingsBase):

    id:int

    class Config:

        from_attributes=True