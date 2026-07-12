# AI Resume Critiquer

## Overview

AI Resume Critiquer is a web application that helps job seekers improve their resumes using AI-powered analysis. Users can upload a resume in PDF or TXT format, specify an optional target job role, and receive detailed feedback on resume quality, strengths, weaknesses, and actionable recommendations.

The application is designed to provide practical suggestions that can help improve resume clarity, ATS compatibility, and overall presentation for internships and professional roles.

## Features

* Upload resumes in PDF or TXT format
* Extract text automatically from uploaded files
* AI-powered resume analysis using the OpenRouter API
* Resume quality rating
* Identification of strengths and weaknesses
* Suggestions for improving content, formatting, and impact
* Role-specific recommendations based on the desired position
* Downloadable feedback report in TXT format
* Responsive and user-friendly Streamlit interface

## Technologies Used

* Python
* Streamlit
* OpenRouter API
* OpenAI Python SDK (configured to communicate with OpenRouter)
* PyPDF2
* python-dotenv
* HTML
* CSS

## How It Works

Deployed here:
https://ai-resume-critiquer-6hthz2gcpmjwigotxsbojv.streamlit.app/
1. Upload a resume in PDF or TXT format.
2. Optionally enter the job role you are targeting.
3. The application extracts the resume text.
4. The extracted content is sent to an AI model through the OpenRouter API.
5. The AI evaluates the resume and returns structured feedback, including:

   * Resume rating
   * Strengths
   * Areas for improvement
   * Content suggestions
   * Role-specific recommendations
6. Users can download the generated feedback as a text report.


## Project Structure

```text
project/
│
├── app.py
├── requirements.txt
├── .env
├── README.md
└── assets/
```
