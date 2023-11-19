import curses
from datetime import datetime
import os

from dotenv import load_dotenv
import requests
from zoom import Client

REFRESH_RATE = 2  # Refresh Rate in SECONDS

load_dotenv()
ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")


class Engagement:
    def __init__(
        self,
        created_time: str,
        engagement_id: str,
        channel_name: str,
        callee_number: str,
        queue_name: str,
        task_priority: int,
        task_status: str,
    ) -> None:
        self.created_time = datetime.fromisoformat(created_time[:-1]).strftime(
            "%H:%M:%S"
        )
        self.engagement_id = engagement_id
        self.channel_name = channel_name
        self.callee_number = callee_number
        self.queue_name = queue_name
        self.task_priority = task_priority
        self.task_status = task_status

    def __str__(self) -> str:
        """Return a string representation of the Engagement object."""

        callee_number = self.callee_number
        queue_name = self.queue_name
        if len(callee_number) > 18:
            callee_number = callee_number[:10] + "..."
        if len(queue_name) > 18:
            queue_name = queue_name[:10] + "..."
        return f"{self.created_time:<15}{self.engagement_id:<26}{self.channel_name:<11}{callee_number:<17}{queue_name:<20}{self.task_priority:<10}{self.task_status:<10}"


class Screen:
    def __init__(self, refresh: int) -> None:
        self.stdscr = curses.initscr()
        self.stdscr.keypad(True)
        self.task_window = curses.newwin(20, curses.COLS - 1, 2, 4)
        curses.halfdelay(refresh * 10)  # halfdelay() requires tenths of a second
        curses.curs_set(False)

    def display_tasks(self, tasks: list[Engagement]) -> None:
        """Write a list of all tasks to the curses window object."""

        self.task_window.clear()
        self.task_window.addstr(
            f"{'Time Entered':<15}{'EngagementID':<26}{'Channel':<11}{'Caller':<17}{'Queue Name':<20}{'Pri':<10}{'Status':<10}\n",
            curses.A_BOLD,
        )
        for task in tasks:
            self.task_window.addstr(f"{str(task)}\n")
        self.stdscr.refresh()
        self.task_window.refresh()

    def close(self) -> None:
        """Close down the curses screen and return the terminal back to previous settings."""

        self.stdscr.keypad(False)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        # curses.curs_set(True)


def get_tasks(client: Client) -> list:
    """Query the ZCC API for all tasks, return a list of active tasks."""

    returned_task_list = []
    endpoint = f"{client.base_url}/contact_center/tasks"
    headers = {"Authorization": f"Bearer {client.token}"}
    params = {"next_page_token": ""}
    try:
        while True:
            if client.token_has_expired:
                client.get_token()
                headers["Authorization"] = f"Bearer {client.token}"
            r = requests.get(endpoint, headers=headers, params=params)
            r.raise_for_status()
            response = r.json()

            # Check that the `tasks` list exists and that the list is not empty.
            if "tasks" in response and response["tasks"]:
                returned_task_list.extend(response["tasks"])

            # Check if further API calls are necessary.
            params["next_page_token"] = response["next_page_token"]
            if not params["next_page_token"]:
                break

    # Handle any errors.
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    return returned_task_list


def process_task_list(task_list: list) -> list[Engagement]:
    task_object_list = []
    for task in task_list:
        # Voice tasks are labelled as `default`, so rename to `voice` for clarity.
        if task["channel_name"] == "default":
            task["channel_name"] = "voice"

        # The Engagement class uses the `callee_number` to display the source of the engagement.
        # Chat tasks don't have a `callee_number`, so copy the `caller_number` instead.
        elif task["channel_name"] == "chat":
            task["callee_number"] = task["caller_number"]

        # Video tasks are labelled `live_video` so rename to `video` for simplicity.
        # There is no `callee_number` field in a video engagement, so create one.
        elif task["channel_name"] == "live_video":
            task["channel_name"] = "video"
            task.setdefault("callee_number", "video_entry")

        # We don't want to see any `cancelled` engagements in the list, so just ignore them.
        if not task["task_status"] == "canceled":
            try:
                task_object_list.append(
                    Engagement(
                        task["created_time"],
                        task["engagement_id"],
                        task["channel_name"],
                        task["callee_number"],
                        task["queue_name"],
                        task["task_priority"],
                        task["task_status"],
                    )
                )
            except KeyError:
                pass
    return task_object_list


def main(screen: Screen) -> None:
    client = Client(CLIENT_ID, CLIENT_SECRET, ACCOUNT_ID)
    client.get_token()
    screen.stdscr.addstr("Press q to quit")
    while True:
        task_list = get_tasks(client)
        print(task_list)
        engagement_list = process_task_list(task_list)
        # print(engagement_list)
        screen.display_tasks(engagement_list)
        key_pressed = screen.stdscr.getch()
        if key_pressed == ord("q"):
            break


if __name__ == "__main__":
    try:
        screen = Screen(REFRESH_RATE)
        main(screen)
        screen.close()
    except:
        screen.close()
