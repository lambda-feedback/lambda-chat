from typing import List, Optional, Union, Dict

# questionSubmissionSummary type
class StudentLatestSubmission:
    def __init__(
        self,
        universalResponseAreaId: Optional[str] = None,
        answer: Optional[str] = None,
        submission: Optional[str] = None,
        feedback: Optional[str] = None,
        rawResponse: Optional[dict] = None,
    ):
        self.universalResponseAreaId = universalResponseAreaId
        self.answer = answer
        self.submission = submission
        self.feedback = feedback
        self.rawResponse = rawResponse

class StudentWorkResponseArea:
    def __init__(
        self,
        publishedPartId: Optional[str] = None,
        publishedPartPosition: Optional[int] = None,
        publishedResponseAreaId: Optional[str] = None,
        publishedResponseAreaPosition: Optional[int] = None,
        responseAreaUniversalId: Optional[str] = None,
        publishedResponseAreaPreResponseText: Optional[str] = None,
        publishedResponseType: Optional[str] = None,
        publishedResponseConfig: Optional[dict] = None,
        totalSubmissions: Optional[int] = None,
        totalWrongSubmissions: Optional[int] = None,
        latestSubmission: Optional[StudentLatestSubmission] = None,
    ):
        self.publishedPartId = publishedPartId
        self.publishedPartPosition = publishedPartPosition
        self.publishedResponseAreaId = publishedResponseAreaId
        self.publishedResponseAreaPosition = publishedResponseAreaPosition
        self.responseAreaUniversalId = responseAreaUniversalId
        self.publishedResponseAreaPreResponseText = publishedResponseAreaPreResponseText
        self.publishedResponseType = publishedResponseType
        self.publishedResponseConfig = publishedResponseConfig
        self.latestSubmission = StudentLatestSubmission(**latestSubmission) if latestSubmission else None
        self.totalSubmissions = totalSubmissions
        self.totalWrongSubmissions = totalWrongSubmissions

# questionInformation type
class ResponseAreaDetails:
    def __init__(
        self,
        id: Optional[str] = None,
        position: Optional[int] = None,
        universalResponseAreaId: Optional[str] = None,
        preResponseText: Optional[str] = None,
        responseType: Optional[str] = None,
        answer: Optional[dict] = None,
        Response: Optional[dict] = None,
    ):
        self.id = id
        self.position = position
        self.universalResponseAreaId = universalResponseAreaId
        self.preResponseText = preResponseText
        self.responseType = responseType
        self.answer = answer
        self.Response = Response

class PartDetails:
    def __init__(
        self,
        publishedPartId: Optional[str] = None,
        publishedPartPosition: Optional[int] = None,
        publishedPartContent: Optional[str] = None,
        publishedPartAnswerContent: Optional[str] = None,
        publishedWorkedSolutionSections: Optional[List[dict]] = [],
        publishedResponseAreas: Optional[List[Optional[ResponseAreaDetails]]] = [],
    ):
        self.publishedPartId = publishedPartId
        self.publishedPartPosition = publishedPartPosition
        self.publishedPartContent = publishedPartContent
        self.publishedPartAnswerContent = publishedPartAnswerContent
        self.publishedWorkedSolutionSections = publishedWorkedSolutionSections
        self.publishedResponseAreas = [ResponseAreaDetails(**publishedResponseArea) for publishedResponseArea in publishedResponseAreas]

class QuestionDetails:
    def __init__(
        self,
        questionTitle: Optional[str] = None,
        questionGuidance: Optional[str] = None,
        questionContent: Optional[str] = None,
        durationLowerBound: Optional[int] = None,
        durationUpperBound: Optional[int] = None,
        parts: Optional[List[PartDetails]] = [],
    ):
        self.questionTitle = questionTitle
        self.questionGuidance = questionGuidance
        self.questionContent = questionContent
        self.durationLowerBound = durationLowerBound
        self.durationUpperBound = durationUpperBound
        self.parts = [PartDetails(**part) for part in parts] 

# questionAccessInformation type
class CurrentPart:
    def __init__(self, id: str = None, position: int = None):
        self.id = id
        self.position = position

class QuestionAccessInformation:
    def __init__(
        self,
        estimatedMinimumTime: Optional[str] = None,
        estimaredMaximumTime: Optional[str] = None,
        timeTaken: Optional[str] = None,
        accessStatus: Optional[str] = None,
        markedDone: Optional[str] = None,
        currentPart: Optional[Dict[str, Union[str, int]]] = {},
    ):
        self.estimatedMinimumTime = estimatedMinimumTime
        self.estimaredMaximumTime = estimaredMaximumTime
        self.timeTaken = timeTaken
        self.accessStatus = accessStatus
        self.markedDone = markedDone
        self.currentPart = CurrentPart(**currentPart)

def convert_index_to_lowercase_letter(index: int) -> str:
    return chr(96 + (index + 1))  # 1-indexed

def parse_json_to_prompt( questionSubmissionSummary: Optional[List[StudentWorkResponseArea]],
                          questionInformation: Optional[QuestionDetails],
                          questionAccessInformation: Optional[QuestionAccessInformation]
                        ) -> Optional[str]:
    
    questionSubmissionSummary = [StudentWorkResponseArea(**submissionsSummary) for submissionsSummary in questionSubmissionSummary]
    questionInformation = QuestionDetails(**questionInformation)
    questionAccessInformation = QuestionAccessInformation(**questionAccessInformation)
    
    if not questionSubmissionSummary or not questionInformation or not questionAccessInformation:
        return None

    def format_response_area_details(responseArea: ResponseAreaDetails, studentSummary: List[StudentWorkResponseArea]) -> str:
        submissionDetails = "\n".join(
            [
                f"My Latest Submission: {ra.latestSubmission.submission};\n"
                f"My Latest Feedback Received: {ra.latestSubmission.feedback};\n"
                f"Total Submissions: {ra.totalSubmissions};\n"
                f"Total Wrong Submissions: {ra.totalWrongSubmissions};\n"
                for ra in studentSummary
                if ra.publishedResponseAreaId == responseArea.id and ra.latestSubmission
            ]
        )

        if not submissionDetails:
            submissionDetails = 'My Latest Submission: none made;'

        return f"""
        ## Response Area: {responseArea.position + 1}
        {f'Area task: What is {responseArea.preResponseText} ?' if responseArea.preResponseText else ''}
        (Secret) Expected Answer: {responseArea.answer};
        {submissionDetails}"""

    def format_part_details(part: PartDetails, currentPartId: str, summary: List[StudentWorkResponseArea]) -> str:
        if not part or not part.publishedResponseAreas:
            return ''

        responseAreas = "\n".join(
            [format_response_area_details(responseArea, summary) for responseArea in part.publishedResponseAreas]
        )

        workedSolutions = (
            "\n".join(
                [
                    f"## Worked Solution {ws.get('position') + 1}: {ws.get('title', '')}\n"
                    f"{ws.get('content', '').strip() or 'No content'}\n"
                    for ws in part.publishedWorkedSolutionSections
                ]
            ) if part.publishedWorkedSolutionSections else f"No worked solutions for part ({convert_index_to_lowercase_letter(part.publishedPartPosition)});"
        )

        return f"""
    # {'[CURRENTLY WORKING ON] ' if currentPartId == part.publishedPartId else ''}Part ({convert_index_to_lowercase_letter(part.publishedPartPosition)}):
    Part Content: {part.publishedPartContent.strip() if part.publishedPartContent else 'No content'};
    {responseAreas}
    {f'Final Part Answer: {part.publishedPartAnswerContent}' if part.publishedPartAnswerContent else 'No direct answer'}
    {workedSolutions}
"""

    questionDetails = f"""This is the question I am currently working on. I am currently working on Part ({convert_index_to_lowercase_letter(questionAccessInformation.currentPart.position)}). Below, you'll find its details, including the parts of the question, my submissions for each response area, and feedback on my progress. This information highlights my efforts and progress so far. 
    Maths equations are in KaTex format, preserve them the same.

# Question: {questionInformation.questionTitle};
    Guidance to Solve the Question: {questionInformation.questionGuidance or 'None'};
    Description of Question: {questionInformation.questionContent};
    Expected Time to Complete the Question: {f'{questionInformation.durationLowerBound} - {questionInformation.durationUpperBound} min;' if questionInformation.durationLowerBound and questionInformation.durationUpperBound else 'No specified duration.'}
    Time Spent on the Question This Session: {questionAccessInformation.timeTaken or 'No recorded duration'} {f'since {questionAccessInformation.markedDone}' if questionAccessInformation.markedDone else ''} {f'which is {questionAccessInformation.accessStatus}' if questionAccessInformation.accessStatus else ''};
    """

    partsDetails = "\n".join(
        [
            format_part_details(
                part,
                questionAccessInformation.currentPart.id,
                questionSubmissionSummary
            ) for part in questionInformation.parts
        ]
    )

    result = f"{questionDetails}\n{partsDetails}".replace("&#x20;&#x20;", "").replace("&#x20", "").replace("\n\n", "\n")

    return result
