from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import pandas as pd
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from linkedin_api import Linkedin

app = Flask(_name_)

# Set your credentials
OPENAI_API_KEY = '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'
EMAIL_ADDRESS = 'jd221brd@gmail.com'
EMAIL_PASSWORD = 'JD1002@221B'
LINKEDIN_EMAIL = 'jd221brd@gmail.com'
LINKEDIN_PASSWORD = 'JD1002@221B'

# Initialize LinkedIn API
linkedin = Linkedin(LINKEDIN_EMAIL, LINKEDIN_PASSWORD)

# Function to fetch Google search results
def fetch_data(query):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    results = []
    for g in soup.find_all('div', class_='tF2Cxc'):
        title = g.find('h3').text
        link = g.find('a')['href']
        results.append({'Name': title, 'Website': link})

    return results

# Function to get lead score using AI
def get_lead_score(company_name, industry):
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"Rate the potential of '{company_name}' in '{industry}' from 1-10."
    response = client.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}]
    )
    return response.choices[0].message["content"]

# Function to get LinkedIn data
def get_linkedin_data(company_name):
    profile_data = []
    profiles = linkedin.search_people(company_name)
    for profile in profiles:
        full_data = linkedin.get_profile(profile['public_id'])
        profile_data.append({
            'Name': full_data['firstName'] + ' ' + full_data['lastName'],
            'LinkedIn': full_data['public_id'],
            'Email': full_data.get('emailAddress', 'N/A'),
            'Phone': full_data.get('phoneNumbers', 'N/A')
        })
    return profile_data

# Function to send email
def send_email(leads):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS
    msg['Subject'] = 'Daily Customer Leads with LinkedIn Contacts'

    body = ""
    for lead in leads:
        body += f"Name: {lead['Name']}\n"
        body += f"Website: {lead['Website']}\n"
        body += f"Lead Score: {lead['Lead Score']}\n"
        body += f"LinkedIn: https://linkedin.com/in/{lead['LinkedIn']}\n"
        body += f"Email: {lead['Email']}\n"
        body += f"Phone: {lead['Phone']}\n"
        body += "-------------------------\n"

    msg.attach(MIMEText(body, 'plain'))
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, msg.as_string())

# API Endpoint
@app.route('/fetch', methods=['POST'])
def fetch():
    data = request.get_json()
    region = data['region']
    industry = data['industry']

    query = f"{industry} in {region}"
    fetched_data = fetch_data(query)

    for company in fetched_data:
        company['Lead Score'] = get_lead_score(company['Name'], industry)
        linkedin_data = get_linkedin_data(company['Name'])
        if linkedin_data:
            company.update(linkedin_data[0])

    send_email(fetched_data)
    return jsonify(fetched_data)

if _name_ == '_main_':
    app.run(host='0.0.0.0', port=5000)