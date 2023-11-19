# zcc-queue-visualiser

## Console-Based Queue Visualiser for Zoom Contact Centre

This script will query the ZCC API for all active tasks (those which are not in a `cancelled` state) and display the results in a table within a curses window. The table will update according to a configurable refresh rate. Information about the ZCC API endpoint used to deliver this functionality can be found here:

<https://marketplace.zoom.us/docs/api-reference/contact-center/methods/#operation/listTasks>

To run this script you must install the modules shown in the **requirements.txt** file by running the following command.

`pip install -r requirements.txt`

Additionally, you must login to <https://marketplace.zoom.us> and create a new Server-to-Server OAuth app with the `contact_center_task:read:admin` scope enabled. Once this is created, open the `.env_sample` file and populate the variables using the values from your Server-to-Server app. **Note**, the use of quotation marks are not required in this file. Save the file as `.env`.

Further information about Server-to-Server OAuth can be found here:

<https://marketplace.zoom.us/docs/guides/build/server-to-server-oauth-app/>
