import fitz  # PyMuPDF
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import spacy
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import os
from collections import defaultdict
from datetime import datetime

class ResumeAnalyzer:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.classifier = LogisticRegression(max_iter=1000)
        self.load_and_train_model()
        
        # Common section headers
        self.section_headers = {
            'summary': ['summary', 'objective', 'profile', 'about'],
            'skills': ['skills', 'technical skills', 'core competencies'],
            'experience': ['experience', 'work experience', 'employment', 'professional experience'],
            'education': ['education', 'academic background', 'qualification'],
            'projects': ['projects', 'project experience', 'portfolio'],
            'certifications': ['certifications', 'certificates', 'accreditations']
        }
        
        # Common skills dictionary
        self.skills_dict = {
            'programming': ['python', 'java', 'javascript', 'c++', 'ruby', 'php', 'typescript', 'swift', 'kotlin'],
            'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'dynamodb'],
            'frameworks': ['django', 'flask', 'react', 'angular', 'vue', 'spring', 'express', 'laravel', 'asp.net'],
            'tools': ['git', 'docker', 'kubernetes', 'jenkins', 'aws', 'azure', 'gcp', 'jira', 'confluence'],
            'data_science': ['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'spark', 'hadoop'],
            'soft_skills': ['leadership', 'communication', 'teamwork', 'problem-solving', 'time management', 'adaptability']
        }

        # Action verbs for experience relevance
        self.action_verbs = [
            'achieved', 'developed', 'implemented', 'managed', 'created', 'improved',
            'increased', 'decreased', 'optimized', 'led', 'coordinated', 'designed',
            'analyzed', 'resolved', 'delivered', 'maintained', 'enhanced', 'streamlined'
        ]

    def load_and_train_model(self):
        # Load the dataset
        try:
            df = pd.read_csv('UpdatedResumeDataSet.csv')
        except FileNotFoundError:
            print("Error: UpdatedResumeDataSet.csv not found. Please ensure the dataset is in the correct directory.")
            # Create a dummy dataframe to prevent further errors
            df = pd.DataFrame({'Resume': ['dummy resume'], 'Category': ['dummy category']})
        
        # Prepare the data
        X = self.vectorizer.fit_transform(df['Resume'])
        y = df['Category']
        
        # Split and train
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.classifier.fit(X_train, y_train)

    def extract_text_from_pdf(self, pdf_path):
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text

    def calculate_ats_score(self, text, filename):
        scores = defaultdict(int)
        feedback = defaultdict(list)
        
        # 1. Keyword Match (25 pts)
        keyword_score = self.analyze_keywords(text)
        scores['keyword_match'] = keyword_score['score']
        feedback['keyword_match'] = keyword_score['feedback']
        
        # 2. Section Presence (10 pts)
        section_score = self.analyze_sections(text)
        scores['section_presence'] = section_score['score']
        feedback['section_presence'] = section_score['feedback']
        
        # 3. Experience Relevance (15 pts)
        exp_score = self.analyze_experience(text)
        scores['experience_relevance'] = exp_score['score']
        feedback['experience_relevance'] = exp_score['feedback']
        
        # 4. Formatting & Readability (10 pts)
        format_score = self.analyze_formatting(text)
        scores['formatting'] = format_score['score']
        feedback['formatting'] = format_score['feedback']
        
        # 5. Grammar & Clarity (10 pts)
        grammar_score = self.analyze_grammar(text)
        scores['grammar'] = grammar_score['score']
        feedback['grammar'] = grammar_score['feedback']
        
        # 6. Contact Information (5 pts)
        contact_score = self.analyze_contact_info(text)
        scores['contact_info'] = contact_score['score']
        feedback['contact_info'] = contact_score['feedback']
        
        # 7. File Naming (5 pts)
        filename_score = self.analyze_filename(filename)
        scores['filename'] = filename_score['score']
        feedback['filename'] = filename_score['feedback']
        
        # 8. Customization (10 pts)
        custom_score = self.analyze_customization(text)
        scores['customization'] = custom_score['score']
        feedback['customization'] = custom_score['feedback']
        
        # Calculate total score
        total_score = sum(scores.values())
        
        return {
            'total_score': total_score,
            'scores': dict(scores),
            'feedback': dict(feedback)
        }

    def analyze_keywords(self, text):
        score = 0
        feedback = []
        found_skills = set()
        
        # Check for skills
        doc = self.nlp(text.lower())
        for token in doc:
            for category, skills in self.skills_dict.items():
                if token.text in skills:
                    found_skills.add(token.text)
        
        # Score based on number of unique skills found
        unique_skills = len(found_skills)
        score = min(unique_skills * 2, 25)  # 2 points per skill, max 25
        
        if unique_skills < 5:
            feedback.append("Add more technical skills to your resume")
        
        return {'score': score, 'feedback': feedback}

    def analyze_sections(self, text):
        score = 0
        feedback = []
        text_lower = text.lower()
        
        # Check for each section type
        for section_type, keywords in self.section_headers.items():
            if any(keyword in text_lower for keyword in keywords):
                score += 2  # 2 points per section, max 10
            else:
                feedback.append(f"Missing {section_type} section")
        
        return {'score': score, 'feedback': feedback}

    def analyze_experience(self, text):
        score = 0
        feedback = []
        
        # Check for action verbs
        action_verb_count = sum(1 for verb in self.action_verbs if verb in text.lower())
        score += min(action_verb_count, 5)  # Up to 5 points for action verbs
        
        # Check for quantified achievements
        achievement_pattern = r'\d+%|\$\d+|\d+x|\d+ times'
        achievements = re.findall(achievement_pattern, text)
        score += min(len(achievements) * 2, 10)  # Up to 10 points for achievements
        
        if action_verb_count < 3:
            feedback.append("Add more action verbs to describe your experience")
        if len(achievements) < 2:
            feedback.append("Include more quantified achievements")
        
        return {'score': score, 'feedback': feedback}

    def analyze_formatting(self, text):
        score = 10  # Start with full points
        feedback = []
        
        # Check for tables (simple heuristic)
        if '|' in text or '\t' in text:
            score -= 2
            feedback.append("Avoid using tables in your resume")
        
        # Check for multiple columns
        if text.count('\n') > 100:  # Simple heuristic for complex formatting
            score -= 2
            feedback.append("Simplify your resume layout")
        
        return {'score': max(0, score), 'feedback': feedback}

    def analyze_grammar(self, text):
        score = 10  # Start with full points
        feedback = []
        
        # Basic grammar checks
        doc = self.nlp(text)
        
        # Check sentence length
        long_sentences = sum(1 for sent in doc.sents if len(sent) > 30)
        if long_sentences > 3:
            score -= 2
            feedback.append("Some sentences are too long")
        
        return {'score': max(0, score), 'feedback': feedback}

    def analyze_contact_info(self, text):
        score = 0
        feedback = []
        
        # Check for email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, text):
            score += 1
        
        # Check for phone
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        if re.search(phone_pattern, text):
            score += 1
        
        # Check for LinkedIn/GitHub
        social_pattern = r'(?:linkedin\.com/in/|github\.com/)[\w-]+'
        if re.search(social_pattern, text):
            score += 1
        
        if score < 3:
            feedback.append("Add more contact information")
        
        return {'score': score, 'feedback': feedback}

    def analyze_filename(self, filename):
        score = 5  # Start with full points
        feedback = []
        
        # Check if filename contains name
        if not re.search(r'[A-Za-z]', filename):
            score -= 2
            feedback.append("Include your name in the filename")
        
        # Check if filename is too generic
        if filename.lower() in ['resume.pdf', 'cv.pdf']:
            score -= 3
            feedback.append("Use a more specific filename (e.g., YourName_Resume.pdf)")
        
        return {'score': max(0, score), 'feedback': feedback}

    def analyze_customization(self, text):
        score = 10  # Start with full points
        feedback = []

        # Analyze if the resume text is generally well-structured and detailed
        # without a specific job description.
        
        # Heuristic 1: Check for adequate length
        if len(text) < 1000:
            score -= 3
            feedback.append("Resume might be too brief; consider adding more detail and examples.")
        
        # Heuristic 2: Check for presence of diverse sections (already covered by section_presence, but reinforces customization)
        # This is a bit redundant with analyze_sections, but serves to emphasize customization quality.
        found_sections = 0
        text_lower = text.lower()
        for section_type, keywords in self.section_headers.items():
            if any(keyword in text_lower for keyword in keywords):
                found_sections += 1
        
        if found_sections < 4:
            score -= 2
            feedback.append("Ensure your resume includes key sections like Summary, Experience, Skills, and Education.")

        # Heuristic 3: Check for specific examples or quantified achievements (reinforces detail)
        achievement_pattern = r'\d+%|\$\d+|\d+x|\d+ times'
        achievements = re.findall(achievement_pattern, text)
        if len(achievements) < 3:
            score -= 2
            feedback.append("Quantify your achievements with numbers, percentages, or metrics whenever possible.")

        return {'score': max(0, score), 'feedback': feedback}

    def analyze_resume(self, pdf_path):
        text = self.extract_text_from_pdf(pdf_path)
        
        # Calculate ATS score components
        ats_analysis = self.calculate_ats_score(text, os.path.basename(pdf_path))
        
        # Predict category
        # Ensure resume_vec is transformed correctly
        if hasattr(self, 'vectorizer') and hasattr(self, 'classifier'):
            resume_vec = self.vectorizer.transform([text])
            predicted_category = self.classifier.predict(resume_vec)[0]
        else:
            predicted_category = "General" # Default category if model not loaded
            print("Warning: TFIDF Vectorizer or Classifier not loaded. Model prediction skipped.")

        # Generate overall assessment
        overall_assessment = self.generate_overall_assessment(ats_analysis)

        # Identify strengths
        strengths = self.identify_strengths(ats_analysis)

        # Identify improvements
        improvements = self.generate_improvement_tips(ats_analysis)
        
        # Extract skills for skills analysis
        all_skills = self.extract_skills(text)
        
        # Filter technical and soft skills based on the skills dictionary
        technical_skills = [s for s in all_skills if any(s in v for k, v in self.skills_dict.items() if k != 'soft_skills')]
        soft_skills = [s for s in all_skills if s in self.skills_dict['soft_skills']]
        
        # Missing skills will now be identified based on general best practices or a predefined list, not job description
        missing_skills = self.identify_missing_skills(all_skills)

        # Generate job recommendations (placeholder)
        job_recommendations = self.generate_recommendations(predicted_category, all_skills)

        response = {
            'ats_score': ats_analysis['total_score'],
            'score_breakdown': ats_analysis['scores'],
            'analysis': {
                'overall_assessment': overall_assessment,
                'strengths': strengths,
                'improvements': improvements
            },
            'job_recommendations': job_recommendations,
            'skills_analysis': {
                'technical': technical_skills,
                'soft': soft_skills,
                'missing': missing_skills
            }
        }
        return response

    def generate_overall_assessment(self, ats_analysis):
        score = ats_analysis['total_score']
        if score >= 80:
            return "Excellent! Your resume is highly optimized for ATS and presents a strong candidate profile."
        elif score >= 60:
            return "Good job! Your resume is generally well-optimized, but there's room for improvement in specific areas."
        elif score >= 40:
            return "Your resume has potential but needs significant optimization to pass ATS and attract recruiters."
        else:
            return "Your resume needs substantial work to meet modern ATS and recruiter expectations."

    def identify_strengths(self, ats_analysis):
        strengths = []
        if ats_analysis['scores']['keyword_match'] >= 20:
            strengths.append("Strong keyword optimization, indicating a good match for target roles.")
        if ats_analysis['scores']['section_presence'] >= 8:
            strengths.append("All essential resume sections are present, ensuring comprehensive information.")
        if ats_analysis['scores']['experience_relevance'] >= 10:
            strengths.append("Well-articulated experience with quantifiable achievements and strong action verbs.")
        if ats_analysis['scores']['formatting'] >= 8:
            strengths.append("Clean and ATS-friendly formatting, enhancing readability.")
        if ats_analysis['scores']['grammar'] >= 8:
            strengths.append("Excellent grammar and clear, concise language.")
        if ats_analysis['scores']['contact_info'] >= 4:
            strengths.append("Complete and easily identifiable contact information.")
        if ats_analysis['scores']['filename'] == 5:
            strengths.append("Professional and appropriate filename.")
        if ats_analysis['scores']['customization'] >= 7:
            strengths.append("Resume appears well-customized and detailed.")
        
        if not strengths:
            strengths.append("No specific strengths identified yet. Focus on all areas for improvement.")

        return strengths

    def identify_missing_skills(self, current_skills):
        # Define a general list of desirable skills that might be missing
        # This can be expanded or made more dynamic over time
        general_desirable_skills = set([
            'project management', 'data analysis', 'cloud computing', 'machine learning',
            'web development', 'mobile development', 'cybersecurity', 'networking',
            'problem-solving', 'critical thinking', 'adaptability', 'teamwork',
            'communication', 'leadership', 'time management', 'customer service'
        ])
        
        missing = []
        current_skills_lower = set(s.lower() for s in current_skills)

        for skill in general_desirable_skills:
            if skill not in current_skills_lower:
                missing.append(skill)

        return missing

    def extract_skills(self, text):
        doc = self.nlp(text.lower())
        extracted_skills = set()
        for category, skills in self.skills_dict.items():
            for skill in skills:
                if skill in text.lower():
                    extracted_skills.add(skill)
        return list(extracted_skills)

    def generate_recommendations(self, role, skills):
        # This would typically come from a job database
        # For now, returning mock data
        mock_jobs = [
            {"title": "Software Engineer", "company": "Tech Solutions Inc.", "location": "San Francisco, CA", "match_score": 90, "link": "#"},
            {"title": "Data Scientist", "company": "Quant Insights LLC", "location": "New York, NY", "match_score": 85, "link": "#"},
            {"title": "Product Manager", "company": "Innovate Corp.", "location": "Seattle, WA", "match_score": 75, "link": "#"},
            {"title": "UX Designer", "company": "Creative Studio", "location": "Austin, TX", "match_score": 70, "link": "#"},
        ]
        return mock_jobs

    def generate_improvement_tips(self, ats_analysis):
        tips = []
        feedback = ats_analysis['feedback']

        if "Add more technical skills to your resume" in feedback['keyword_match']:
            tips.append("Strengthen your resume by integrating more industry-specific technical keywords relevant to your target roles.")
        if "Missing summary section" in feedback['section_presence']:
            tips.append("Include a concise professional summary or objective statement at the top of your resume.")
        if "Missing skills section" in feedback['section_presence']:
            tips.append("Add a dedicated skills section to highlight your technical and soft skills clearly.")
        if "Missing experience section" in feedback['section_presence']:
            tips.append("Ensure you have a detailed 'Experience' or 'Work History' section.")
        if "Missing education section" in feedback['section_presence']:
            tips.append("Include an 'Education' section with your degrees, institutions, and dates.")
        if "Add more action verbs to describe your experience" in feedback['experience_relevance']:
            tips.append("Use strong action verbs (e.g., 'Developed', 'Managed', 'Achieved') to describe your accomplishments.")
        if "Include more quantified achievements" in feedback['experience_relevance']:
            tips.append("Quantify your accomplishments with numbers, percentages, or metrics whenever possible.")
        if "Avoid using tables in your resume" in feedback['formatting']:
            tips.append("Remove tables and complex formatting elements that can be difficult for ATS to parse.")
        if "Simplify your resume layout" in feedback['formatting']:
            tips.append("Opt for a clean, simple, and standard resume layout for optimal ATS compatibility.")
        if "Some sentences are too long" in feedback['grammar']:
            tips.append("Break down long sentences for better readability and clarity.")
        if "Add more contact information" in feedback['contact_info']:
            tips.append("Ensure your resume includes essential contact details: email, phone number, and a LinkedIn profile URL.")
        if "Include your name in the filename" in feedback['filename']:
            tips.append("Rename your resume file to include your full name (e.g., 'JohnDoe_Resume.pdf').")
        if "Use a more specific filename" in feedback['filename']:
            tips.append("Avoid generic filenames like 'resume.pdf'; use a more descriptive name.")
        if "Provide a job description to get a customization score." in feedback['customization']:
            # This tip will now be removed since job description is not provided
            pass
        if "Tailor your resume more closely to the job description by including relevant keywords and phrases." in feedback['customization']:
            tips.append("Review your resume to ensure it's well-detailed and comprehensively covers your experiences.")
        
        return tips

    def generate_feedback_pdf(self, analysis_data, output_path=None):
        """Generate a PDF report with the analysis results"""
        if output_path:
            c = canvas.Canvas(output_path, pagesize=letter)
        else:
            # Create a PDF in memory
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
        
        # Set up the PDF
        width, height = letter
        margin = 50
        current_y = height - margin
        
        # Title
        c.setFont("Helvetica-Bold", 24)
        c.drawString(margin, current_y, "Resume Analysis Report")
        current_y -= 40
        
        # ATS Score
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, current_y, "ATS Score")
        current_y -= 25
        
        c.setFont("Helvetica", 12)
        score_text = f"Overall Score: {analysis_data['ats_score']['total_score']}/100"
        c.drawString(margin, current_y, score_text)
        current_y -= 25
        
        # Score Breakdown
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, current_y, "Score Breakdown")
        current_y -= 25
        
        c.setFont("Helvetica", 10)
        for category, score in analysis_data['ats_score']['scores'].items():
            category_text = f"{category.replace('_', ' ').title()}: {score} points"
            c.drawString(margin + 20, current_y, category_text)
            current_y -= 20
            
            # Add feedback for this category
            if category in analysis_data['ats_score']['feedback']:
                feedback = analysis_data['ats_score']['feedback'][category]
                if feedback:
                    c.setFont("Helvetica-Oblique", 9)
                    for item in feedback:
                        if current_y < margin + 50:  # Check if we need a new page
                            c.showPage()
                            current_y = height - margin
                        c.drawString(margin + 40, current_y, f"• {item}")
                        current_y -= 15
                    c.setFont("Helvetica", 10)
        
        # Skills Analysis
        if current_y < margin + 100:  # Check if we need a new page
            c.showPage()
            current_y = height - margin
            
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, current_y, "Skills Analysis")
        current_y -= 25
        
        c.setFont("Helvetica", 10)
        for category, skills in analysis_data['skills_analysis'].items():
            if current_y < margin + 50:  # Check if we need a new page
                c.showPage()
                current_y = height - margin
                
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margin, current_y, category.replace('_', ' ').title())
            current_y -= 20
            
            c.setFont("Helvetica", 10)
            skills_text = ", ".join(skills)
            self._draw_multiline_string(c, skills_text, margin + 20, current_y, width - 2 * margin)
            current_y -= 40
        
        # Job Recommendations
        if current_y < margin + 100:  # Check if we need a new page
            c.showPage()
            current_y = height - margin
            
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, current_y, "Job Recommendations")
        current_y -= 25
        
        c.setFont("Helvetica", 10)
        for job in analysis_data['job_recommendations']:
            if current_y < margin + 100:  # Check if we need a new page
                c.showPage()
                current_y = height - margin
                
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margin, current_y, job['title'])
            current_y -= 20
            
            c.setFont("Helvetica", 10)
            self._draw_multiline_string(c, job['description'], margin + 20, current_y, width - 2 * margin)
            current_y -= 40
        
        # Save the PDF
        c.save()
        
        if not output_path:
            buffer.seek(0)
            return buffer
        return output_path

    def _draw_multiline_string(self, canvas, text, x, y, max_width):
        from reportlab.lib.enums import TA_LEFT
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import getSampleStyleSheet

        styles = getSampleStyleSheet()
        style = styles['Normal']
        style.alignment = TA_LEFT
        style.leading = 14
        style.fontSize = 12
        style.textColor = self.get_current_fill_color(canvas)

        p = Paragraph(text, style)
        
        # Calculate height dynamically
        text_width, text_height = p.wrapOn(canvas, max_width, 1000)
        
        p.drawOn(canvas, x, y - text_height) # Adjust y to draw from top left

    def _draw_list_items(self, canvas, items, x, y, max_width):
        for item in items:
            self._draw_multiline_string(canvas, f"- {item}", x + 10, y, max_width - 10) # Indent bullets
            y -= (len(item.split('\n')) * 14) + 5 # Adjust y for next item
            
    # Helper to get current fill color (Reportlab doesn't expose it directly)
    def get_current_fill_color(self, canvas):
        # This is a bit of a hack, but Reportlab's canvas doesn't directly expose current fill color
        # We'll just return a default or infer based on what's set in generate_feedback_pdf
        # For this context, assuming text is always dark gray unless explicitly changed
        return (0.2, 0.2, 0.2) # Default to dark gray 