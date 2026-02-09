from langchain_core.messages import BaseMessage, SystemMessage

from src.infrastructure.prompt.base_prompt_manager import BasePromptManager


class PersonaPromptManager(BasePromptManager):

    def build_analyse_user_prompt(
        self,
        user_prompt: str,
        previous_segments: str,
    ) -> list[BaseMessage]:
        """Build the prompt for analysing the user prompt to find relevant user segments."""
        template = self.get_template('user_segment_search', 'analyse_user_prompt.md')
        system_prompt = template.format(
            user_prompt=user_prompt,
            previous_segments=previous_segments,
        )
        return [SystemMessage(content=system_prompt)]

    def build_find_user_segment_prompt(
        self,
        user_prompt: str,
        analysis_result: str | None,
    ) -> list[BaseMessage]:
        """Build the prompt for finding user segments based on the analysed user prompt."""
        template = self.get_template('user_segment_search', 'find_user_segment.md')
        output_example = self.get_template('user_segment_search', 'find_user_segment_output_example.md')

        system_prompt = template.format(
            user_prompt=user_prompt,
            analysis_result=analysis_result,
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_verify_user_segment_prompt(
        self,
        segment_name: str,
        unifying_problem_segment: str | None,
        where_to_find_segment: str | None,
        segment_description: str,
    ) -> list[BaseMessage]:
        """Build the prompt for verifying the found user segment."""
        template = self.get_template('user_segment_search', 'verify_user_segment.md')
        output_example = self.get_template('user_segment_search', 'verify_user_segment_output_example.md')

        system_prompt = template.format(
            segment_name=segment_name,
            unifying_problem_segment=unifying_problem_segment,
            where_to_find_segment=where_to_find_segment,
            segment_description=segment_description,
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]
