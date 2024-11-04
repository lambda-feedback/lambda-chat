def get_student_submissions_by_response_area(conn, student_id, response_area_id):
    """
    Get all submissions by a specific student for a specific response area.
    """
    try:
        with conn.cursor() as cur:
            # Define and execute the query
            cur.execute(
                """
                SELECT * 
                FROM public."Submission"
                WHERE "userId" = %s
                  AND "responseAreaId" = %s;
                """,
                (student_id, response_area_id)
            )

            # Fetch all results
            submissions = cur.fetchall()
            return submissions

    except Exception as e:
        print(f"Error executing query: {e}")
        return None

def count_nb_submissions(submissions):
    """
    Count the number of correct, incorrect and total submissions.
    submission['grade'] is an integer, 0 for incorrect and 1 for correct.
    """
    submissions_grades = [submission[4] for submission in submissions]
    return {
        'correct': len([grade for grade in submissions_grades if grade == 1]),
        'incorrect': len([grade for grade in submissions_grades if grade == 0]),
        'total': len(submissions)
    }

# try:
#     from .query_utils import connect
# except ImportError:
#     from evaluation_function.db_analytics.query_utils import connect
# if __name__ == '__main__':
#     # Connect to the database
#     conn = connect()
#     if conn:
#         # Example inputs
#         student_id = 'test'  # Replace with the specific student ID
#         module_slug = 'TEST_SANDBOX'  # Replace with specific module slug
#         set_name = 'TESTSet'  # Replace with the set name
#         response_area_id = 'test'  # Replace with specific question ID #response area

#         # Query the number of submissions
#         submissions = (get_student_submissions_by_response_area(conn, student_id, response_area_id))
#         submission_count = count_nb_submissions(submissions)
#         print(f"Number of submissions by student {student_id}: {submission_count}")

#         # Close the connection
#         conn.close()
