from typing import Any, Optional, Dict

class LinkedInBotState:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.credentials_set = False
        self.api_key_set = False
        self.job_application_profile_set = False
        self.gpt_answerer_set = False
        self.parameters_set = False
        self.logged_in = False

    def validate_state(self, required_keys: list[str]) -> None:
        for key in required_keys:
            if not getattr(self, key):
                raise ValueError(f"{key.replace('_', ' ').capitalize()} must be set before proceeding.")

class LinkedInBotFacade:
    def __init__(self, login_component: Any, apply_component: Any) -> None:
        self.login_component = login_component
        self.apply_component = apply_component
        self.state = LinkedInBotState()
        self.job_application_profile: Any = None
        self.resume: Any = None
        self.email: Optional[str] = None
        self.password: Optional[str] = None
        self.parameters: Optional[Dict[str, Any]] = None

    def set_job_application_profile_and_resume(self, job_application_profile: Any, resume: Any) -> None:
        self._validate_non_empty(job_application_profile, "Job application profile")
        self._validate_non_empty(resume, "Resume")
        self.job_application_profile = job_application_profile
        self.resume = resume
        self.state.job_application_profile_set = True

    def set_secrets(self, email: str, password: str) -> None:
        self._validate_non_empty(email, "Email")
        self._validate_non_empty(password, "Password")
        self.email = email
        self.password = password
        self.state.credentials_set = True

    def set_gpt_answerer_and_resume_generator(self, gpt_answerer_component: Any, resume_generator_manager: Any) -> None:
        self._ensure_job_profile_and_resume_set()
        gpt_answerer_component.set_job_application_profile(self.job_application_profile)
        gpt_answerer_component.set_resume(self.resume)
        self.apply_component.set_gpt_answerer(gpt_answerer_component)
        self.apply_component.set_resume_generator_manager(resume_generator_manager)
        self.state.gpt_answerer_set = True

    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        self._validate_non_empty(parameters, "Parameters")
        self.parameters = parameters
        self.apply_component.set_parameters(parameters)
        self.state.parameters_set = True

    def start_login(self) -> None:
        self.state.validate_state(["credentials_set"])
        self.login_component.set_secrets(self.email, self.password)
        self.login_component.start()
        self.state.logged_in = True

    def start_apply(self) -> None:
        self.state.validate_state(["logged_in", "job_application_profile_set", "gpt_answerer_set", "parameters_set"])
        self.apply_component.start_applying()

    def _validate_non_empty(self, value: Any, name: str) -> None:
        if not value:
            raise ValueError(f"{name} cannot be empty.")

    def _ensure_job_profile_and_resume_set(self) -> None:
        if not self.state.job_application_profile_set:
            raise ValueError("Job application profile and resume must be set before proceeding.")
