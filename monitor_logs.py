import csv # this module is used to work with the csv format of the log file
from pprint import pprint # this module is used to print in a more readeable format the dictionary when needed


# the first function parses the input csv file and creates a dictionary containing inner dictionaries grouped on the jobs IDs and the needed data for each one
def transform_csv_into_dictionary(input_file):

    dict_grouped_by_pid = {} # init the empty dict where jobs will be stored 

    try:
        with open(input_file, mode='r', newline='', encoding='utf-8') as csvfile: # standard opening of the csv file in read mode
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



# I am implementing the main work as functions and in main() I only call them
def main():

    input_file = "logs.log"

    parsed_results = transform_csv_into_dictionary(input_file)

    pprint(parsed_results)


if __name__ == "__main__":
    main()