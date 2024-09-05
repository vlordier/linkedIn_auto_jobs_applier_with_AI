from typing import Dict, List, Optional, Union
from typing_extensions import Literal
from linkedin_api import Linkedin
from urllib.parse import urlencode
import logging

# set log to all debug
logging.basicConfig(level=logging.INFO)

class LinkedInEvolvedAPI(Linkedin):
    already_applied_jobs: List[str] = []

    def __init__(self, username, password):
        super().__init__(username, password)

    def search_jobs(
        self,
        keywords: Optional[str] = None,
        companies: Optional[List[str]] = None,
        experience: Optional[List[Literal["1", "2", "3", "4", "5", "6"]]] = None,
        job_type: Optional[List[Literal["F", "C", "P", "T", "I", "V", "O"]]] = None,
        job_title: Optional[List[str]] = None,
        industries: Optional[List[str]] = None,
        location_name: Optional[str] = None,
        remote: Optional[List[Union[Literal["1"], Literal["2"], Literal["3"]]]] = None,
        listed_at=24 * 60 * 60,
        distance: Optional[int] = None,
        easy_apply: Optional[bool] = True,
        limit=-1,
        offset=0,
        **kwargs,
    ) -> List[Dict]:
        """Perform a LinkedIn search for jobs.

        :param keywords: Search keywords (str)
        :type keywords: str, optional
        :param companies: A list of company URN IDs (str)
        :type companies: list, optional
        :param experience: A list of experience levels, one or many of "1", "2", "3", "4", "5" and "6" (internship, entry level, associate, mid-senior level, director and executive, respectively)
        :type experience: list, optional
        :param job_type:  A list of job types , one or many of "F", "C", "P", "T", "I", "V", "O" (full-time, contract, part-time, temporary, internship, volunteer and "other", respectively)
        :type job_type: list, optional
        :param job_title: A list of title URN IDs (str)
        :type job_title: list, optional
        :param industries: A list of industry URN IDs (str)
        :type industries: list, optional
        :param location_name: Name of the location to search within. Example: "Kyiv City, Ukraine"
        :type location_name: str, optional
        :param remote: Filter for remote jobs, onsite or hybrid. onsite:"1", remote:"2", hybrid:"3"
        :type remote: list, optional
        :param listed_at: maximum number of seconds passed since job posting. 86400 will filter job postings posted in last 24 hours.
        :type listed_at: int/str, optional. Default value is equal to 24 hours.
        :param distance: maximum distance from location in miles
        :type distance: int/str, optional. If not specified, None or 0, the default value of 25 miles applied.
        :param easy_apply: filter for jobs that are easy to apply to
        :type easy_apply: bool, optional. Default value is True.
        :param limit: maximum number of results obtained from API queries. -1 means maximum which is defined by constants and is equal to 1000 now.
        :type limit: int, optional, default -1
        :param offset: indicates how many search results shall be skipped
        :type offset: int, optional
        :return: List of jobs
        :rtype: list
        """
        count = Linkedin._MAX_SEARCH_COUNT
        if limit is None:
            limit = -1

        query: dict[str, Union[str, dict[str, str]]] = {
            "origin": "JOB_SEARCH_PAGE_QUERY_EXPANSION"
        }
        if keywords:
            query["keywords"] = "KEYWORD_PLACEHOLDER"
        if location_name:
            query["locationFallback"] = "LOCATION_PLACEHOLDER"

        query["selectedFilters"] = {}
        if companies:
            query["selectedFilters"]["company"] = f"List({','.join(companies)})"
        if experience:
            query["selectedFilters"]["experience"] = f"List({','.join(experience)})"
        if job_type:
            query["selectedFilters"]["jobType"] = f"List({','.join(job_type)})"
        if job_title:
            query["selectedFilters"]["title"] = f"List({','.join(job_title)})"
        if industries:
            query["selectedFilters"]["industry"] = f"List({','.join(industries)})"
        if distance:
            query["selectedFilters"]["distance"] = f"List({distance})"
        if remote:
            query["selectedFilters"]["workplaceType"] = f"List({','.join(remote)})"
        if easy_apply:
            query["selectedFilters"]["applyWithLinkedin"] = "List(true)"

        query["selectedFilters"]["timePostedRange"] = f"List(r{listed_at})"
        query["spellCorrectionEnabled"] = "true"

        query_string = (
            str(query)
            .replace(" ", "")
            .replace("'", "")
            .replace("KEYWORD_PLACEHOLDER", keywords or "")
            .replace("LOCATION_PLACEHOLDER", location_name or "")
            .replace("{", "(")
            .replace("}", ")")
        )
        results = []
        while True:
            if limit > -1 and limit - len(results) < count:
                count = limit - len(results)
            default_params = {
                "decorationId": "com.linkedin.voyager.dash.deco.jobs.search.JobSearchCardsCollection-174",
                "count": count,
                "q": "jobSearch",
                "query": query_string,
                "start": len(results) + offset,
            }

            res = self._fetch(
                f"/voyagerJobsDashJobCards?{urlencode(default_params, safe='(),:')}",
                headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
            )
            data = res.json()

            elements = data.get("included", [])
            new_data = []
            for e in elements:
                trackingUrn = e.get("trackingUrn")
                if trackingUrn:
                    trackingUrn = trackingUrn.split(":")[-1]
                    e["job_id"] = trackingUrn
                if e.get("$type") == "com.linkedin.voyager.dash.jobs.JobPosting":
                    new_data.append(e)

            if not new_data:
                break
            results.extend(new_data)
            if (
                (-1 < limit <= len(results))
                or len(results) / count >= Linkedin._MAX_REPEATED_REQUESTS
            ) or len(elements) == 0:
                break

            self.logger.debug(f"results grew to {len(results)}")

        return results

    def get_fields_for_easy_apply(self,job_id: str) -> List[Dict]:
        """Get fields needed for easy apply jobs.

        :param job_id: Job ID
        :type job_id: str
        :return: Fields
        :rtype: dict
        """

        cookies = self.client.session.cookies.get_dict()
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])

        headers: Dict[str, str] = self._headers()


        headers["Accept"] = "application/vnd.linkedin.normalized+json+2.1"
        headers["csrf-token"] = cookies["JSESSIONID"].replace('"', "")
        headers["Cookie"] = cookie_str
        headers["Connection"] = "keep-alive"


        default_params = {
            "decorationId": "com.linkedin.voyager.dash.deco.jobs.OnsiteApplyApplication-67",
            "jobPostingUrn": f"urn:li:fsd_jobPosting:{job_id}",
            "q": "jobPosting",
        }

        default_params = urlencode(default_params)
        res = self._fetch(
            f"/voyagerJobsDashOnsiteApplyApplication?{default_params}",
            headers=headers,
            cookies=cookies,
        )

        match res.status_code:
            case 200:
                pass
            case 409:
                self.logger.error("Failed to fetch fields for easy apply job because already applied to this job!")
                return []
            case _:
                self.logger.error("Failed to fetch fields for easy apply job")
                return []

        try:
            data = res.json()
        except ValueError:
            self.logger.error("Failed to parse JSON response")
            return []

        form_components = []

        for item in data.get("included", []):
            if "formComponent" in item:
                urn = item["urn"]
                try:
                    title = item["title"]["text"]
                except TypeError:
                    title = urn

                form_component_type = list(item["formComponent"].keys())[0]
                form_component_details = item["formComponent"][form_component_type]

                component_info = {
                    "title": title,
                    "urn": urn,
                    "formComponentType": form_component_type,
                }

                if "textSelectableOptions" in form_component_details:
                    options = [
                        opt["optionText"]["text"] for opt in form_component_details["textSelectableOptions"]
                    ]
                    component_info["selectableOptions"] = options
                elif "selectableOptions" in form_component_details:
                    options = [
                        opt["textSelectableOption"]["optionText"]["text"]
                        for opt in form_component_details["selectableOptions"]
                    ]
                    component_info["selectableOptions"] = options

                form_components.append(component_info)

        return form_components

    def apply_to_job(self,job_id: str, fields: dict, followCompany: bool = True) -> bool:
        return False

        # ToDo: Implement apply to job parser first
        # How need to be implemented:
        # 1. Get fields for easy apply job from the previous method (get_fields_for_easy_apply)
        # 2. Fill the fields with the data adding a response parameter in the specific field in the dict object, for example:
        # {'title': 'Quanti anni di esperienza di lavoro hai con Router?', 'urn': 'urn:li:fsd_formElement:urn:li:jobs_applyformcommon_easyApplyFormElement:(4013860791,9478711764,numeric)', 'formComponentType': 'singleLineTextFormComponent'}
        # Became:
        # {'title': 'Quanti anni di esperienza di lavoro hai con Router?', 'urn': 'urn:li:fsd_formElement:urn:li:jobs_applyformcommon_easyApplyFormElement:(4013860791,9478711764,numeric)', 'formComponentType': 'singleLineTextFormComponent', 'response': '5'}
        # To fill, you can temporary use input() function to get the data from the user manually for testing purposes (for the further implementation, the question will be asked to AI implementation and automatically filled)
        # Build a working payload.

        # EXAMPLE OF WORKING PAYLOAD
        # 4005350454 is job_id, so need to be replaced with the job_id

        #{
        #    "followCompany": true,
        #    "responses": [
        #        {
        #            "formElementUrn": "urn:li:fsd_formElement:urn:li:jobs_applyformcommon_easyApplyFormElement:(4005350454,3497278561,multipleChoice)",
        #            "formElementInputValues": [
        #                {
        #                    "entityInputValue": {
        #                        "inputEntityName": "email@gmail.com"
        #                    }
        #                }
        #            ]
        #        },
        #        {
        #            "formElementUrn": "urn:li:fsd_formElement:urn:li:jobs_applyformcommon_easyApplyFormElement:(4005350454,3497278545,phoneNumber~country)",
        #            "formElementInputValues": [
        #                {
        #                    "entityInputValue": {
        #                        "inputEntityName": "Italy (+39)",
        #                        "inputEntityUrn": "urn:li:country:it"
        #                    }
        #                }
        #            ]
        #        },
        #        {
        #            "formElementUrn": "urn:li:fsd_formElement:urn:li:jobs_applyformcommon_easyApplyFormElement:(4005350454,3497278545,phoneNumber~nationalNumber)",
        #            "formElementInputValues": [
        #                {
        #                    "textInputValue": "3333333"
        #                }
        #            ]
        #        },
        #        {
        #            "formElementUrn": "urn:li:fsd_formElement:urn:li:jobs_applyformcommon_easyApplyFormElement:(4005350454,3497278529,multipleChoice)",
        #            "formElementInputValues": [
        #                {
        #                    "entityInputValue": {
        #                        "inputEntityName": "Native or bilingual"
        #                    }
        #                }
        #            ]
        #        },
        #        {
        #            "formElementUrn": "urn:li:fsd_formElement:urn:li:jobs_applyformcommon_easyApplyFormElement:(4005350454,3497278537,numeric)",
        #            "formElementInputValues": [
        #                {
        #                    "textInputValue": "0"
        #                }
        #            ]
        #        },
        #        {
        #            "formElementUrn": "urn:li:fsd_formElement:urn:li:jobs_applyformcommon_easyApplyFormElement:(4005350454,3498546713,multipleChoice)",
        #            "formElementInputValues": [
        #                {
        #                    "entityInputValue": {
        #                        "inputEntityName": "No"
        #                    }
        #                }
        #            ]
        #        },
        #        {
        #            "formElementUrn": "urn:li:fsd_formElement:urn:li:jobs_applyformcommon_easyApplyFormElement:(4005350454,3497278521,multipleChoice)",
        #            "formElementInputValues": [
        #                {
        #                    "entityInputValue": {
        #                        "inputEntityName": "No"
        #                    }
        #                }
        #            ]
        #        }
        #    ],
        #    "referenceId": "",
        #    "trackingCode": "d_flagship3_search_srp_jobs",
        #    "fileUploadResponses": [
        #        {
        #            "inputUrn": "urn:li:fsd_resume:/##todo##",
        #            "formElementUrn": "urn:li:fsu_jobApplicationFileUploadFormElement:urn:li:jobs_applyformcommon_easyApplyFormElement:(4005350454,3497278553,document)"
        #        }
        #    ],
        #    "trackingId": ""
        #}

        # Push the commit to the repository and create a pull request to the v3 branch.

    def set_job_as_applied(self, job_id: str) -> None:
        self.already_applied_jobs.append(job_id)







## EXAMPLE USAGE
if __name__ == "__main__":
    api: LinkedInEvolvedAPI = LinkedInEvolvedAPI(username="", password="")
    jobs = api.search_jobs(keywords="Frontend Developer", location_name="Italia", limit=5, easy_apply=True, offset=1)
    for job in jobs:
        job_id: str = job["job_id"]
        if job_id in api.already_applied_jobs:
            logging.info(f"Already applied to job {job_id}, skipping it")
            continue

        fields = api.get_fields_for_easy_apply(job_id)
        for field in fields:
            print(field)
        break
