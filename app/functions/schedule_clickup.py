import os
import json
import requests
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
from pydantic import ValidationError




# LLM / Instructor imports
from groq import Groq
import instructor


# ClickUp API Configuration
CLICKUP_API_KEY = os.environ.get("CLICKUP_API_KEY", "your_clickup_api_key")
BASE_URL = "https://api.clickup.com/api/v2"




# Pydantic Models
class Subtask(BaseModel):
   name: str
   description: Optional[str] = None
   start_date: Optional[int] = None
   due_date: Optional[int] = None
   priority: Optional[int] = None
   link: Optional[str] = None
   depends_on: Optional[List[str]] = None




class Task(BaseModel):
   name: str
   description: Optional[str] = None
   start_date: Optional[int] = None
   due_date: Optional[int] = None
   priority: Optional[int] = None
   link: Optional[str] = None
   depends_on: Optional[List[str]] = None
   subtasks: List[Subtask] = []




class TaskList(BaseModel):
   list_name: str
   tasks: List[Task] = []




class Schedule(BaseModel):
   schedule_name: str
   lists: List[TaskList] = []




def _headers():
   return {
       "Authorization": CLICKUP_API_KEY,
       "Content-Type": "application/json"
   }




def generate_schedule(prompt: str) -> Schedule:
   """
   Generates a schedule from the prompt using an LLM (Groq + Instructor).
   """
   template = f"""
   You are a helpful assistant that generates a JSON representation of a 'Schedule' object.
   The 'Schedule' object includes:

   - schedule_name (str)
   - lists (list of 'TaskList')

   Each 'TaskList' has:
   - list_name (str)
   - tasks (list of 'Task')

   Each 'Task' includes:
   - name (str)
   - description (optional str)
   - start_date (optional int, UNIX timestamp in seconds)
   - due_date (optional int, UNIX timestamp in seconds)
   - priority (optional int: 0=none, 1=low, 2=normal, 3=high, 4=urgent)
   - link (optional str)
   - depends_on (optional list of strings referencing other tasks by name)
   - subtasks (list of 'Subtask')


   User's Prompt: {prompt}


   Output: A *valid JSON* that can be parsed into a 'Schedule' object using Pydantic.
   """


   llm_api_key = os.environ.get("GROQ_API_KEY")
   if not llm_api_key:
       raise EnvironmentError("Missing GROQ_API_KEY environment variable.")
   groq_client = Groq(api_key=llm_api_key)
   llm_client = instructor.from_groq(groq_client)


   # 1. Make request to LLM
   response = llm_client.chat.completions.create(
       model="llama3-groq-70b-8192-tool-use-preview",
       messages=[{"role": "user", "content": template}],
       response_model=Schedule
   )


   # 2. Parse and validate the output
   llm_output_str = response.model_dump_json()


   try:
       llm_output_dict = json.loads(llm_output_str)
   except json.JSONDecodeError as e:
       raise ValueError(f"LLM did not return valid JSON. Error: {e}")


   try:
       schedule = Schedule.model_validate(llm_output_dict)
   except ValidationError as e:
       raise ValueError(f"Generated JSON does not conform to the Schedule model. Error: {e}")


   return schedule




def create_folder(space_id: str, folder_name: str) -> str:
   url = f"{BASE_URL}/space/{space_id}/folder"
   payload = {"name": folder_name}
   resp = requests.post(url, json=payload, headers=_headers())
   if resp.status_code == 200:
       return resp.json().get("id")
   else:
       raise Exception(f"Error creating folder '{folder_name}': {resp.status_code} - {resp.text}")




def create_list(folder_id: str, list_name: str) -> str:
   url = f"{BASE_URL}/folder/{folder_id}/list"
   payload = {"name": list_name}
   resp = requests.post(url, json=payload, headers=_headers())
   if resp.status_code == 200:
       return resp.json().get("id")
   else:
       raise Exception(f"Error creating list '{list_name}': {resp.status_code} - {resp.text}")




def create_task(list_id: str, task: Task) -> str:
   url = f"{BASE_URL}/list/{list_id}/task"
   payload = task.dict(exclude_unset=True)
   resp = requests.post(url, json=payload, headers=_headers())
   if resp.status_code == 200:
       return resp.json().get("id")
   else:
       raise Exception(f"Error creating task '{task.name}': {resp.status_code} - {resp.text}")




def set_dependency(task_id: str, depends_on_id: str):
   url = f"{BASE_URL}/task/{task_id}/dependency"
   payload = {"depends_on": depends_on_id}
   resp = requests.post(url, json=payload, headers=_headers())
   if resp.status_code != 200:
       raise Exception(f"Error setting dependency for task {task_id} on {depends_on_id}: {resp.status_code} - {resp.text}")




def process_schedule(space_id: str, schedule: Schedule):
   """
   Creates a ClickUp schedule from the validated Schedule object.
   1) Create a folder
   2) Create lists, tasks, and subtasks
   3) Set dependencies if required
   """


   folder_id = create_folder(space_id, schedule.schedule_name)
   name_to_id_map = {}


   for task_list in schedule.lists:
       list_id = create_list(folder_id, task_list.list_name)


       for task in task_list.tasks:
           task_id = create_task(list_id, task)
           name_to_id_map[task.name] = task_id


           for subtask in task.subtasks:
               subtask_id = create_task(list_id, subtask)
               name_to_id_map[subtask.name] = subtask_id


   # Second pass to set dependencies
   for task_list in schedule.lists:
       for task in task_list.tasks:
           current_task_id = name_to_id_map[task.name]
           if task.depends_on:
               for dep_name in task.depends_on:
                   if dep_name in name_to_id_map:
                       set_dependency(current_task_id, name_to_id_map[dep_name])


           for subtask in task.subtasks:
               current_subtask_id = name_to_id_map[subtask.name]
               if subtask.depends_on:
                   for dep_name in subtask.depends_on:
                       if dep_name in name_to_id_map:
                           set_dependency(current_subtask_id, name_to_id_map[dep_name])


def transform_llm_output(llm_output):
   try:
       # Validate the output against the Schedule model
       schedule = Schedule.model_validate(llm_output)
       return schedule
   except ValidationError as e:
       print(f"Validation error: {e}")
       # Logic to transform the output manually if required
       # For simplicity, reformat data here or raise an exception
       raise ValueError("LLM output does not match the expected format.")

# Main function only runs if the script is executed directly
if __name__ == "__main__":
   user_prompt = "Create a weekly cleaning and meal schedule that harmonizes the order and efficiency of household management. Be as detailed as possible."
   print("Generating schedule from the LLM...")
   generated_schedule = generate_schedule(user_prompt)
   print("\nGenerated Schedule (parsed via Pydantic):")
   print(generated_schedule.model_dump_json(indent=2))


   space_id = "your_clickup_space_id"
   print("\nCreating schedule in ClickUp...")
   process_schedule(space_id, generated_schedule)
   print("Done!")

