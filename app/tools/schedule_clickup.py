"""
ClickUp Scheduling Tool
Manages the creation and scheduling of tasks within ClickUp.
"""

import os
import httpx
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
from dotenv import load_dotenv

# Load API keys from environment
load_dotenv()
CLICKUP_API_KEY = os.getenv("CLICKUP_API_KEY")
BASE_URL = "https://api.clickup.com/api/v2"

# Pydantic models for task management
class Subtask(BaseModel):
    name: str
    description: Optional[str]
    start_date: Optional[int]
    due_date: Optional[int]
    priority: Optional[int]
    link: Optional[str]
    depends_on: Optional[List[str]] = None

class Task(BaseModel):
    name: str
    description: Optional[str]
    start_date: Optional[int]
    due_date: Optional[int]
    priority: Optional[int]
    link: Optional[str]
    depends_on: Optional[List[str]] = None
    subtasks: Optional[List[Subtask]] = []

class TaskList(BaseModel):
    list_name: str
    tasks: List[Task]

class Schedule(BaseModel):
    schedule_name: str
    lists: List[TaskList]

class ScheduleClickUpTool:
    """A tool to create and manage ClickUp schedules."""

    def __init__(self):
        self.headers = {"Authorization": CLICKUP_API_KEY, "Content-Type": "application/json"}

    async def create_folder(self, space_id: str, folder_name: str):
        """Create a new folder in ClickUp."""
        url = f"{BASE_URL}/space/{space_id}/folder"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"name": folder_name}, headers=self.headers)
        if response.status_code == 200:
            return response.json().get("id")
        raise Exception(f"Error creating folder: {response.json()}")

    async def create_list(self, folder_id: str, list_name: str):
        """Create a new list inside a folder."""
        url = f"{BASE_URL}/folder/{folder_id}/list"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"name": list_name}, headers=self.headers)
        if response.status_code == 200:
            return response.json().get("id")
        raise Exception(f"Error creating list: {response.json()}")

    async def create_task(self, list_id: str, task: Task):
        """Create a task in a ClickUp list."""
        url = f"{BASE_URL}/list/{list_id}/task"
        payload = task.dict(exclude_unset=True)
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
        if response.status_code == 200:
            return response.json().get("id")
        raise Exception(f"Error creating task: {response.json()}")

    async def create_schedule(self, data: dict):
        """
        Create a full schedule in ClickUp.
        Expects data to match the Schedule model schema.
        """
        try:
            schedule = Schedule(**data)
            space_id = os.getenv("CLICKUP_SPACE_ID")
            folder_id = await self.create_folder(space_id, schedule.schedule_name)
            for task_list in schedule.lists:
                list_id = await self.create_list(folder_id, task_list.list_name)
                for task in task_list.tasks:
                    await self.create_task(list_id, task)
            return {"status": "success", "message": "Schedule created successfully."}
        except ValidationError as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": str(e)}