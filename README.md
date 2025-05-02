***Python Log Monitoring App***

You can run the application by cloning the repository and running `python3 monitoring_app.py`.

## Code Explanation

1.  **Read and Group Logs (`transform_csv_into_dictionary`):**
    * Opens the input CSV file (`logs.log`).
    * Reads each row line by line.
    * Uses the `unique ID` (PID) from the 4th column as a key in a dictionary (`dict_grouped_by_pid`).
    * For each PID, it stores the job description and uses the status string (e.g., `' START'`, `' END'`) as inner keys, storing the corresponding timestamp string as the value. If a status appears multiple times for the same PID, the *last* timestamp encountered is kept.

![creating_dicts_iamge](https://github.com/user-attachments/assets/72de9dfc-6e54-4fb1-9f06-5723423268a4)

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
  
![write_to_output_prints](https://github.com/user-attachments/assets/26a06913-f24e-4a14-856c-dd2305f115f3)


## Testing Strategy

To ensure the reliability and correctness of the log processing application, a comprehensive test suite was developed using the `pytest` framework, with assistance in structuring and refining the tests.
For pytest to work, you need to install it by running `python3 -m pip install -r requirements.txt`

The testing approach covers several key areas:

1.  **Unit Tests:** Individual functions responsible for core logic transformations were tested in isolation:
    * `timestamps_from_string_to_time`: Verified correct conversion of time strings to `time` objects and handling of invalid formats.
    * `substract_times`: Tested accurate duration calculation, including edge cases like midnight wrap-around and negative durations (where end time precedes start time on the same day).
    * `alert_if_thresholds_passed`: Ensured the correct alert level (0, 1, or 2) is returned based on various job duration inputs compared to the 5 and 10-minute thresholds.

2.  **File Parsing Tests:**
    * `transform_csv_into_dictionary`: Tested the function's ability to correctly parse sample CSV data (provided via fixtures) into the expected dictionary structure. Scenarios included valid data, files with missing END records, and files with duplicate START records (verifying the latest timestamp is kept). File not found and empty file cases were also checked.

3.  **Output and Integration Tests:**
    * `prepare_and_write_output_to_file`: Tested the main processing function's behavior across different scenarios using pre-defined job dictionaries:
        * Jobs completing within acceptable time limits.
        * Jobs triggering WARNING messages (5-10 minutes).
        * Jobs triggering ERROR messages (>10 minutes).
        * Jobs missing START or END records.
    * These tests verified both the console output (using `pytest`'s `capsys` fixture) and the content written to the output file (using `pytest`'s `tmp_path` fixture for temporary files).

4.  **Test Techniques:**
    * `@pytest.fixture`: Used extensively to provide sample CSV content and manage test setup.
    * `@pytest.mark.parametrize`: Employed to efficiently run unit tests with multiple input/output combinations.
    * `tmp_path` and `capsys`: Leveraged built-in `pytest` fixtures for handling temporary files/directories and capturing console output, respectively.

![tests_passed](https://github.com/user-attachments/assets/5452947b-e575-4990-8d58-9749241d7913)
