import os
import json
import pandas as pd
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI()

def load_json(file_path):
    """Loads the JSON data from the specified file path."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def parse_trials(data):
    """Parses the JSON data to extract relevant trial information and tracks exclusions."""
    records = []
    exclusions = []  # List to track excluded trials with reasons

    if isinstance(data, dict):
        full_studies = data.get('FullStudiesResponse', {}).get('FullStudies', [])
    elif isinstance(data, list):
        full_studies = data
    else:
        print("Unexpected JSON structure.")
        return pd.DataFrame(records), exclusions

    for trial in full_studies:
        try:
            protocol_section = trial.get('protocolSection', {})
            identification_module = protocol_section.get('identificationModule', {})
            brief_title = identification_module.get('briefTitle', '')
            nct_id = identification_module.get('nctId', '')

            status_module = protocol_section.get('statusModule', {})
            overall_status = status_module.get('overallStatus', '')
            start_date = status_module.get('startDateStruct', {}).get('date', '')
            primary_completion_date = status_module.get('primaryCompletionDateStruct', {}).get('date', '')

            description_module = protocol_section.get('descriptionModule', {})
            brief_summary = description_module.get('briefSummary', '')

            conditions_module = protocol_section.get('conditionsModule', {})
            conditions = conditions_module.get('conditions', [])

            contacts_locations_module = protocol_section.get('contactsLocationsModule', {})
            central_contacts = contacts_locations_module.get('centralContacts', [])
            contact_info = '; '.join([
                f"{contact.get('name', '')} ({contact.get('role', '')}): {contact.get('phone', 'N/A')} / {contact.get('email', 'N/A')}"
                for contact in central_contacts
            ])

            # Extract location information
            locations = contacts_locations_module.get('locations', [])
            location_info = '; '.join([
                f"{loc.get('facility', '')}, {loc.get('city', '')}, {loc.get('state', '')}, {loc.get('country', '')}"
                for loc in locations
            ])

            eligibility_module = protocol_section.get('eligibilityModule', {})
            eligibility_criteria = eligibility_module.get('eligibilityCriteria', '')

            trial_record = {
                'NCTId': nct_id,
                'Title': brief_title,
                'Status': overall_status,
                'Start Date': start_date,
                'Primary Completion Date': primary_completion_date,
                'BriefSummary': brief_summary,
                'Conditions': ', '.join(conditions),
                'Contact Info': contact_info,
                'Location': location_info,
                'Eligibility Criteria': eligibility_criteria
            }

            # Step-by-step filtering logic
            exclusion_reason = None

            # Check for excluded keywords in the title
            exclude_keywords = ['fusion', 'surgery', 'screw', 'discectomy']
            if any(keyword in brief_title.lower() for keyword in exclude_keywords):
                exclusion_reason = "Title contains 'fusion', 'surgery', 'screw', or 'discectomy'"

            # Check for cervical or thoracic focus without lumbar relevance
            if not exclusion_reason and (
                ('cervical' in brief_title.lower() or 'thoracic' in brief_title.lower())
                and 'lumbar' not in brief_title.lower()
                and 'lumbar' not in brief_summary.lower()
            ):
                exclusion_reason = "Only targets cervical or thoracic spine"

            # Check for potential irrelevance using a simple model call
            irrelevant_title_keywords = ['diabetic', 'eye', 'hearing', 'pulmonary', 'cardiac', 'psych', 'dermatology']
            if not exclusion_reason and any(keyword in brief_title.lower() for keyword in irrelevant_title_keywords):
                is_relevant = check_relevance_with_ai(brief_title, brief_summary)
                if not is_relevant:
                    exclusion_reason = "Deemed irrelevant by AI"

            if exclusion_reason:
                exclusions.append({'NCTId': nct_id, 'Title': brief_title, 'Reason': exclusion_reason})
            else:
                records.append(trial_record)

        except Exception as e:
            print(f"Error parsing trial {nct_id}: {e}")
            continue

    df = pd.DataFrame(records)
    return df, pd.DataFrame(exclusions)


def check_relevance_with_ai(title, description):
    """Calls OpenAI API to check if the title and description indicate a relevant study."""
    try:
        prompt = (
            f"Given the following clinical trial title and brief description, determine if the trial is relevant to spinal "
            f"health, particularly involving the spine or lumbar region. Respond with 'relevant' or 'irrelevant'.\n\n"
            f"Title: {title}\n"
            f"Description: {description}\n"
        )
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant specializing in evaluating clinical trial relevance."},
                {"role": "user", "content": prompt}
            ]
        )
        response = completion.choices[0].message.content.strip().lower()
        return response == 'relevant'
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return True  # Assume relevant if the API call fails

def display_trials(df):
    """Displays a numbered list of trial titles."""
    print("\nList of Relevant Clinical Trials:")
    for idx, title in enumerate(df['Title'], start=1):
        print(f"{idx}. {title}")

def display_exclusions(exclusions_df):
    """Displays the excluded trials sorted by reason."""
    if exclusions_df.empty:
        print("\nNo trials were excluded.")
        return

    print("\nList of Excluded Trials by Reason:")
    for reason in exclusions_df['Reason'].unique():
        print(f"\nReason: {reason}")
        relevant_exclusions = exclusions_df[exclusions_df['Reason'] == reason]
        for _, row in relevant_exclusions.iterrows():
            print(f"- {row['Title']} (NCTId: {row['NCTId']})")

    input("\nPress Enter to return to the main menu...")

def display_full_trial_info(df, index):
    """Displays the full information of the selected trial."""
    trial = df.iloc[index]
    trial_info = (
        f"NCTId: {trial['NCTId']}\n"
        f"Title: {trial['Title']}\n"
        f"Status: {trial['Status']}\n"
        f"Start Date: {trial['Start Date']}\n"
        f"Primary Completion Date: {trial['Primary Completion Date']}\n"
        f"Brief Summary: {trial['BriefSummary']}\n"
        f"Conditions: {trial['Conditions']}\n"
        f"Contact Info: {trial['Contact Info']}\n"
        f"Location: {trial['Location']}\n"
        f"Eligibility Criteria: {trial['Eligibility Criteria']}\n"
    )
    print(trial_info)
    return trial_info  # Return the full trial info for ChatGPT context

def get_chatgpt_response(trial_info, question):
    """Calls the OpenAI API to get a response based on the full trial information and question."""
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant knowledgeable about clinical trials."},
                {"role": "user", "content": f"Here is detailed information about a clinical trial:\n\n{trial_info}\n\nNow, answer the following question:\n{question}"}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "An error occurred while communicating with the AI."

def keyword_search(df, keyword):
    """Searches for a keyword in the Title, BriefSummary, and Conditions columns of the DataFrame."""
    keyword = keyword.lower()
    matches = df[
        df['Title'].str.contains(keyword, case=False, na=False) |
        df['BriefSummary'].str.contains(keyword, case=False, na=False) |
        df['Conditions'].str.contains(keyword, case=False, na=False)
    ]

    if matches.empty:
        print(f"\nNo trials found containing the keyword '{keyword}'.")
    else:
        print(f"\nTrials containing the keyword '{keyword}':")
        for idx, row in matches.iterrows():
            trial_number = df.index.get_loc(idx) + 1  # Get the trial number from the main menu index
            print(f"{trial_number}. {row['Title']} (NCTId: {row['NCTId']})")
            if keyword in row['Title'].lower():
                print("  * Found in Title")
            if keyword in row['BriefSummary'].lower():
                print("  * Found in Brief Summary")
            if keyword in row['Conditions'].lower():
                print("  * Found in Conditions")


def main():
    json_file_path = 'C:/Users/Stephen/my-website/ctg-studies.json'  # Adjust this path as needed

    if not os.path.exists(json_file_path):
        print(f"JSON file not found at {json_file_path}. Please check the path.")
        return

    print("Loading JSON data...")
    data = load_json(json_file_path)

    print("Parsing trials...")
    df, exclusions_df = parse_trials(data)
    print(f"Total relevant trials parsed: {len(df)}")

    if df.empty:
        print("No relevant trials found.")
        return

    while True:
        print("\nMain Menu:")
        print("1. View relevant clinical trials")
        print("2. View excluded trials")
        print("3. Search for a keyword in relevant trials")
        user_input = input("\nEnter the number to choose an option, or type 'exit' to leave: ")

        if user_input.lower() == 'exit':
            print("Exiting the program.")
            break
        elif user_input == '1':
            display_trials(df)
            trial_input = input("\nEnter the number of the trial to view its information (or press Enter to return to the main menu): ")
            if trial_input.isdigit():
                num = int(trial_input)
                if 1 <= num <= len(df):
                    trial_info = display_full_trial_info(df, num - 1)
                    while True:
                        question = input("\nAsk a question about this trial or type 'back' to return to the main menu: ")
                        if question.lower() == 'back':
                            break
                        else:
                            response = get_chatgpt_response(trial_info, question)
                            print("\nChatGPT Response:")
                            print(response)
        elif user_input == '2':
            display_exclusions(exclusions_df)
        elif user_input == '3':
            keyword = input("\nEnter a keyword to search for: ")
            if keyword.strip():
                keyword_search(df, keyword)
            else:
                print("Please enter a valid keyword.")
        else:
            print("Invalid input. Please enter a valid number or type 'exit' to leave.")

if __name__ == "__main__":
    main()
