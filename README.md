***Python Log Monitoring App***

1.  **Read and Group Logs (`transform_csv_into_dictionary`):**
    * Opens the input CSV file (`logs.log`).
    * Reads each row line by line.
    * Uses the `unique ID` (PID) from the 4th column as a key in a dictionary (`dict_grouped_by_pid`).
    * For each PID, it stores the job description and uses the status string (e.g., `' START'`, `' END'`) as inner keys, storing the corresponding timestamp string as the value. If a status appears multiple times for the same PID, the *last* timestamp encountered is kept.

2.  **Calculate Duration:**
    * **`timestamps_from_string_to_time`:** Converts the timestamp *strings* (like "10:05:30") stored in the dictionary into Python `time` objects.
    * **`substract_times`:** Takes the start and end `time` objects. It combines them with an arbitrary date to create `datetime` objects (necessary for subtraction). It calculates the difference, adding 1 day to the end time if it appears earlier than the start time *and* looks like a midnight crossing (e.g., start PM, end AM), ensuring correct duration calculation even across days.

3.  **Check Thresholds (`alert_if_thresholds_passed`):**
    * Takes the calculated job duration (`timedelta` object).
    * Compares it against pre-defined `timedelta` objects for 5 minutes and 10 minutes.
    * Returns `1` if the duration is over 5 minutes but not over 10.
    * Returns `2` if the duration is over 10 minutes.
    * Returns `0` otherwise (duration is 5 minutes or less).

4.  **Process and Write Output (`prepare_and_write_output_to_file`):**
    * Iterates through the grouped dictionary (`jobs_dictionary`).
    * For each Job ID, it retrieves the START and END timestamps (using `.get()` to handle cases where one might be missing, defaulting to 'Not Found').
    * If both START and END timestamps are found:
        * It calls the functions to convert timestamps and calculate `lasting_time`.
        * It calls `alert_if_thresholds_passed` with the `lasting_time`.
        * Based on the return value (0, 1, or 2):
            * If `1` (over 5 min): Writes a "WARNING" message (including job description, PID, and duration) to the output file (`output.out`).
            * If `2` (over 10 min): Writes an "ERROR" message (including job description, PID, and duration) to the output file.
            * If `0`: Prints an "acceptable" message to the console only.
    * It also prints status updates and details to the console for each job processed.
    * Handles cases where START or END times are missing by printing messages to the console.