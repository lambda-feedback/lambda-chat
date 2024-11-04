"""
Gather all DB data on the user and ready it for LLM prompt insertion.
"""

try:
    from .query_utils import connect
    from .nb_submissions import get_student_submissions_by_response_area, count_nb_submissions
except ImportError:
    from evaluation_function.db_analytics.query_utils import connect
    from evaluation_function.db_analytics.nb_submissions import get_student_submissions_by_response_area, count_nb_submissions

LLM_prompt = """Student's progress on the question:
- Number of submissions: {submission_count}
- Number of correct submissions: {correct}
- Number of incorrect submissions: {incorrect}
"""

def get_student_data(student_id, response_area_id):

    conn = connect()
    if conn:
        # Query the number of submissions
        submissions = (get_student_submissions_by_response_area(conn, student_id, response_area_id))
        submission_count = count_nb_submissions(submissions)
        print(f"Number of submissions by student {student_id}: {submission_count}")

        # Close the connection
        conn.close()

        return LLM_prompt.format(
            submission_count=submission_count['total'],
            correct=submission_count['correct'],
            incorrect=submission_count['incorrect']
        )


if __name__ == '__main__':
    # Example inputs
    student_id = 'test'  # Replace with the specific student ID
    response_area_id = 'test'  # Replace with specific question ID #response area

    print(get_student_data(student_id, response_area_id))