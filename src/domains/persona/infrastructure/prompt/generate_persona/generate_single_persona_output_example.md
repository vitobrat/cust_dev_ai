{
"$schema": "http://json-schema.org/draft-07/schema#",
"type": "object",
"required": \[
"personal_info_block",
"problem_block",
"social_block",
"psychographic_behavior_block"
\],
"properties": {
"personal_info_block": {
"type": "object",
"required": \[
"name",
"age",
"marital_status",
"gender"
\],
"properties": {
"name": {
"type": "string",
"description": "Full name. Should be culturally appropriate for the persona's background."
},
"age": {
"type": "integer",
"description": "Specific age. Ensure it aligns with the professional/social stage of the segment."
},
"marital_status": {
"type": "string",
"description": "Detailed status: e.g., 'Divorced with shared custody of two teens', 'Single, living in a co-living space'."
},
"gender": {
"type": "string",
"enum": \[
"male",
"female"
\],
"description": "The biological gender of the persona."
}
}
},
"problem_block": {
"type": "object",
"required": \[
"persona_specific_problem",
"problem_spendings",
"person_suffering",
"is_manage_budget"
\],
"properties": {
"persona_specific_problem": {
"type": "string",
"description": "A highly specific, detailed manifestation of the segment's problem in this person's life. Describe a concrete situation where they face this issue."
},
"problem_spendings": {
"type": "string",
"description": "Quantify the loss. Mention specific time (e.g., '4 hours every Monday') and money (e.g., '$150/month on manual workarounds') they currently waste."
},
"person_suffering": {
"type": "string",
"description": "The emotional and professional toll. Does it cause burnout, fear of being fired, frustration with teammates, or loss of sleep? Be visceral."
},
"is_manage_budget": {
"type": "boolean",
"description": "True if this specific persona has the financial authority or personal funds to pay for a solution."
}
}
},
"social_block": {
"type": "object",
"required": \[
"geographical_location",
"education",
"social_status",
"profession"
\],
"properties": {
"geographical_location": {
"type": "string",
"enum": \[
"village",
"small_town",
"medium_sized_town",
"large_town",
"city"
\],
"description": "The type of settlement where the persona resides."
},
"education": {
"type": "string",
"description": "The level of education, specific degree name, and a description of the institution or context (e.g., 'MSc in Physics from ETH Zurich' or 'Self-taught through YouTube bootcamps')."
},
"social_status": {
"type": "string",
"description": "Their standing in society, lifestyle habits, and how they interact with their peer group (e.g., 'Respected senior member of a local hiking club, middle-class income')."
},
"profession": {
"type": "string",
"description": "Detailed job role and industry. If applicable, describe their specific daily responsibilities or status as a homemaker/student."
}
}
},
"psychographic_behavior_block": {
"type": "object",
"required": \[
"psychological_profile",
"idealogical_beliefs",
"technology_adoption",
"communication_style"
\],
"properties": {
"psychological_profile": {
"type": "string",
"description": "Deep psychological traits: include their values, typical reactions to stress, and personality archetypes (e.g., 'Highly conscientious, risk-averse, values stability over growth')."
},
"idealogical_beliefs": {
"type": "string",
"description": "Their internal compass: political leanings, religious views, and cultural values that might influence their buying decisions."
},
"technology_adoption": {
"type": "string",
"description": "Their position on the adoption curve (Innovator to Laggard). Describe their comfort level, preferred devices, and 'must-have' software or platforms."
},
"communication_style": {
"type": "string",
"description": "How they talk and listen. Preferred methods (text, voice, face-to-face) and the tone they use (e.g., 'Skeptical and direct, uses heavy industry jargon, hates small talk')."
}
}
}
}
}
