from pydantic import BaseModel

class Settings(BaseModel):
    sqlite_path: str = r"E:\0-Automated-Apps\Shasta-DB\data\archive.sqlite"
    initial_root_name: str = "for_doni"
    initial_root_path: str = r"D:\Google Drive\For Doni"

settings = Settings()
