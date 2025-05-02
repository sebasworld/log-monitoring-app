import csv # this module is used to work with the csv format of the log file
from pprint import pprint # this module is used to print in a more readeable format the dictionary when needed
from datetime import datetime, date, timedelta


# the first function parses the input csv file and creates a dictionary containing inner dictionaries grouped on the jobs IDs and the needed data for each one
def transform_csv_into_dictionary(input_file):

    dict_grouped_by_pid = {} # init the empty dict where jobs will be stored 

    try:
        with open(input_file, mode='r', newline='', encoding='utf-8') as csvfile: # standard usage of with open of the csv file in read mode so that it also closes when the sequence ends 
            reader = csv.reader(csvfile, delimiter=',') # created a csv object called 'reader' where I also specified how the columns are delimited 

            for i, row in enumerate(reader):
                timestamp_string = row[0]
                job_description = row[1]
                job_status = row[2]
                job_pid = row[3]
                if job_pid not in dict_grouped_by_pid: # only if the found PID is new, I create a new key with it in the dictionary
                    dict_grouped_by_pid[job_pid] = {' DESCRIPTION': job_description} # I always create the new keys by also creating an inner dict containing the assigned DESCRIPTION - this one can be theoretically ignored as I am using the PID for identifying each job, but I am saving it for a more detailed output log

                dict_grouped_by_pid[job_pid][job_status] = timestamp_string # after creating the PID key containing also the DESCRIPTION, I am also using now the job status as another inner key to which I am giving the value of the timestamp
                                                                            # when iterating over the rows of the csv, it will find both statuses of a job, and for each one it will create new key:value pair with the desired timestamp
    except FileNotFoundError:
        print(f"Error: File not found at '{input_file}'")
        return None

    except Exception as e:
        print(f"An unexpected error occurred while reading '{input_file}': {e}")
        return None

    return dict_grouped_by_pid # the function returns the complete dict with all inner dicts


# this basic function serves for converting the timestamps which are extracted as strings into datetime objects
def timestamps_from_string_to_time(timestamp):

    datetime_object = datetime.strptime(timestamp, '%H:%M:%S')
    time_object = datetime_object.time()

    return time_object


# this function handles the substraction between 2 datetime objects
def substract_times(start_time, end_time):

    arbitrary_date = date.today() # based on the research I did, a datetime object needs to be combined with an arbitrary date so the '-' operator can work when doing substractions
    datetime1 = datetime.combine(arbitrary_date, start_time)
    datetime2 = datetime.combine(arbitrary_date, end_time)

    difference = datetime2 - datetime1

    return difference


# this function handles the comparison of the lasting time of a job which will be used for issueing a warning / error log message
def alert_if_thresholds_passed(job_lasting_time):

    five_minutes = timedelta(minutes=5) # I create here the time objects of 5 and 10 minutes used below for comparison
    ten_minutes = timedelta(minutes=10)

    is_over_five_minutes = job_lasting_time > five_minutes # the function receives as parameter the lasting time of a job, here I create the needed boolean variables based on each comparison
    is_over_ten_minutes = job_lasting_time > ten_minutes

    if is_over_five_minutes and not is_over_ten_minutes:
        return 1 # I return 1 if a job lasted over 5 mins but below 10 - so I know when to issue a Warning
    elif is_over_ten_minutes:
        return 2 # I return 2 if a job lasted over 10 mins so that I can issue an Error

    return 0 # If a job lasting time does not verify one of the above conditions (mainly being less than 5 minutes) then I return 0


# this function manipulates the data and writes to the output file the proper warnings / errors based on the input log file
def prepare_and_write_output_to_file(jobs_dictionary, output_filename):
    try:
        with open(output_filename, mode='w', encoding='utf-8') as output_file: # using 'with open' to write into the output file and close it automatically at the end of the sequence

            for job_id, items in jobs_dictionary.items(): # here I am manually parsing the dict: I am retrieving each PID and its coresponding items

                start_time = items.get(' START', 'Not Found') # I am accesing the PIDs items by their key names, if they are not found - the variables will hold the str 'Not Found'
                end_time = items.get(' END', 'Not Found')
                job_descr = items.get(' DESCRIPTION', 'Not Found')

                print(f"PID: {job_id}, Job DESCRIPTION: {job_descr}")
                print(f"  START Timestamp: {start_time}")
                print(f"  END Timestamp:{end_time}")

                if end_time == 'Not Found': # here I am tackling the scenario where a job started but hasn't finished (if the END time is not found, I assume its not finished)
                    print("  This JOB didn't END!")
                else:
                    lasting_time = substract_times(timestamps_from_string_to_time(start_time), timestamps_from_string_to_time(end_time)) # if both Start and End timestamps are found, I make use of the other functions to get the time difference between them

                    print(f"  Job lasting time: {lasting_time}")
                    alert_buffer = alert_if_thresholds_passed(lasting_time) # retrieving here the value of 0,1,2 from the alert function and then check below which scenario we have

                    if alert_buffer == 0:
                        print("  JOB lasting time was acceptable!") # if the value is 0, then the JOB lasting time was under 5 minutes, no logged messages here
                    elif alert_buffer == 1: # if the job took over 5 mins but under 10 mins, then I am writing to the output file a warning LOG message
                        message = f"WARNING - JOB '{job_descr}' with PID:{job_id} LASTED FOR MORE THAN 5 MINUTES! ({lasting_time})\n"
                        output_file.write(message)
                        print(f"  WARNING - JOB '{job_descr}' with PID:{job_id} LASTED FOR MORE THAN 5 MINUTES!")
                    elif alert_buffer == 2: # same logic for the over 10 mins scenario - I am logging here an Error in the output file
                        message = f"ERROR - JOB '{job_descr}' with PID:{job_id} LASTED FOR MORE THAN 10 MINUTES! ({lasting_time})\n"
                        output_file.write(message)
                        print(f"  ERROR - JOB '{job_descr}' with PID:{job_id} LASTED FOR MORE THAN 10 MINUTES!")
                print("-" * 25)
    except IOError as e:
        print(f"Error opening or writing to output file '{output_filename}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}")


# the implementation is split in functions and below in main() I only call them
def main():

    input_file = "logs.log"
    output_file = "output.out"

    dictionary_from_csv = transform_csv_into_dictionary(input_file)

    pprint(dictionary_from_csv)

    # here I tested the new functions by using the hardcoded values of the first PID from the dictionary
    print(substract_times(timestamps_from_string_to_time(dictionary_from_csv['37980'][' START']),timestamps_from_string_to_time(dictionary_from_csv['37980'][' END'])))

    prepare_and_write_output_to_file(dictionary_from_csv, output_file)

if __name__ == "__main__":
    main()