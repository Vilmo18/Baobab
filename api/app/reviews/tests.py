from datetime import datetime
import json
import itertools

from app import db, LOGGER
from app.utils.testing import ApiTestCase
from app.events.models import Event, EventRole
from app.users.models import AppUser, UserCategory, Country
from app.applicationModel.models import ApplicationForm, Question, Section
from app.responses.models import Response, Answer, ResponseReviewer
from app.reviews.models import ReviewForm, ReviewQuestion, ReviewQuestionTranslation, ReviewResponse, ReviewScore, ReviewConfiguration
from app.utils.errors import REVIEW_RESPONSE_NOT_FOUND, FORBIDDEN, USER_NOT_FOUND
from nose.plugins.skip import SkipTest
from app.organisation.models import Organisation

from parameterized import parameterized

class ReviewsApiTest(ApiTestCase):
    
    def seed_static_data(self):
        self.add_organisation('Deep Learning Indaba 2019', 'blah.png', 'blah_big.png')
        self.add_organisation('Deep Learning Indaba 2020', 'blah.png', 'blah_big.png')
        user_categories = [
            UserCategory('Honours'),
            UserCategory('Student'),
            UserCategory('MSc'),
            UserCategory('PhD')
        ]
        db.session.add_all(user_categories)
        db.session.commit()

        countries = [
            Country('Egypt'),
            Country('Botswana'),
            Country('Namibia'),
            Country('Zimbabwe'),
            Country('Mozambique'),
            Country('Ghana'),
            Country('Nigeria')
        ]
        db.session.add_all(countries)
        db.session.commit()
        
        reviewer1 = AppUser('r1@r.com', 'reviewer', '1', 'Mr', password='abc', organisation_id=1,)
        reviewer2 = AppUser('r2@r.com', 'reviewer', '2', 'Ms',  password='abc', organisation_id=1,)
        reviewer3 = AppUser('r3@r.com', 'reviewer', '3', 'Mr',  password='abc', organisation_id=1,)
        reviewer4 = AppUser('r4@r.com', 'reviewer', '4', 'Ms', password='abc', organisation_id=1,)
        candidate1 = AppUser('c1@c.com', 'candidate', '1', 'Mr',  password='abc', organisation_id=1,)
        candidate2 = AppUser('c2@c.com', 'candidate', '2', 'Ms',  password='abc', organisation_id=1,)
        candidate3 = AppUser('c3@c.com', 'candidate', '3', 'Mr',  password='abc', organisation_id=1,)
        candidate4 = AppUser('c4@c.com', 'candidate', '4', 'Ms',  password='abc', organisation_id=1,)
        system_admin = AppUser('sa@sa.com', 'system_admin', '1', 'Ms', password='abc', organisation_id=1, is_admin=True)
        event_admin = AppUser('ea@ea.com', 'event_admin', '1', 'Ms', password='abc',organisation_id=1)
        users = [reviewer1, reviewer2, reviewer3, reviewer4, candidate1, candidate2, candidate3, candidate4, system_admin, event_admin]
        for user in users:
            user.verify()
        db.session.add_all(users)
        db.session.commit()

        events = [
            self.add_event({'en': 'indaba 2019'}, {'en': 'The Deep Learning Indaba 2019, Kenyatta University, Nairobi, Kenya '}, datetime(2019, 8, 25), datetime(2019, 8, 31),
            'KENYADABA2019'),
            self.add_event({'en': 'indaba 2020'}, {'en': 'The Deep Learning Indaba 2018, Stellenbosch University, South Africa'}, datetime(2018, 9, 9), datetime(2018, 9, 15),
            'INDABA2020', 2)
        ]
        db.session.commit()

        event_roles = [
            EventRole('admin', 10, 1),
            EventRole('reviewer', 3, 1)
        ]
        db.session.add_all(event_roles)
        db.session.commit()

        application_forms = [
            self.create_application_form(1, True, False),
            self.create_application_form(2, False, False)
        ]
        db.session.add_all(application_forms)
        db.session.commit()

        sections = [
            Section(1, 1),
            Section(2, 1)
        ]
        db.session.add_all(sections)
        db.session.commit()

        options = [
            {
                "value": "indaba-2017",
                "label": "Yes, I attended the 2017 Indaba"
            },
            {
                "value": "indaba-2018",
                "label": "Yes, I attended the 2018 Indaba"
            },
            {
                "value": "indaba-2017-2018",
                "label": "Yes, I attended both Indabas"
            },
            {
                "value": "none",
                "label": "No"
            }
        ]
        questions = [
            Question(1, 1, 1, 'long_text'),
            Question(1, 1, 2, 'long_text'),
            Question(2, 2, 1, 'long_text'),
            Question(2, 2, 2, 'long_text'),
            Question(1, 1, 3, 'multi-choice')
        ]
        db.session.add_all(questions)
        db.session.commit()

        self.add_question_translation(1, 'en', 'Question 1')
        self.add_question_translation(2, 'en', 'Question 2')
        self.add_question_translation(3, 'en', 'Question 3')
        self.add_question_translation(4, 'en', 'Question 4')
        self.add_question_translation(5, 'en', 'Did you attend the 2017 or 2018 Indaba', options=options)

        closed_review = ReviewForm(2, datetime(2018, 4, 30))
        closed_review.close()
        review_forms = [
            ReviewForm(1, datetime(2019, 4, 30)),
            closed_review
        ]
        db.session.add_all(review_forms)
        db.session.commit()

        review_configs = [
            ReviewConfiguration(review_form_id=review_forms[0].id, num_reviews_required=3, num_optional_reviews=0),
            ReviewConfiguration(review_form_id=review_forms[1].id, num_reviews_required=3, num_optional_reviews=0)
        ]
        db.session.add_all(review_configs)
        db.session.commit()

        review_questions = [
            ReviewQuestion(1, 1, 'multi-choice', True, 1, 0),
            ReviewQuestion(1, 2, 'multi-choice', True, 2, 0),
            ReviewQuestion(2, 3, 'multi-choice', True, 1, 0),
            ReviewQuestion(2, 4, 'information', False, 2, 0)
        ]
        db.session.add_all(review_questions)
        db.session.commit()

        review_question_translations = [
            ReviewQuestionTranslation(review_questions[0].id, 'en'),
            ReviewQuestionTranslation(review_questions[0].id, 'fr'),
            ReviewQuestionTranslation(review_questions[1].id, 'en', headline='English Headline', description='English Description', placeholder='English Placeholder', options=[{'label': 'en1', 'value': 'en'}], validation_regex='EN Regex', validation_text='EN Validation Message'),
            ReviewQuestionTranslation(review_questions[1].id, 'fr', headline='French Headline', description='French Description', placeholder='French Placeholder', options=[{'label': 'fr1', 'value': 'fr'}], validation_regex='FR Regex', validation_text='FR Validation Message'),
            ReviewQuestionTranslation(review_questions[2].id, 'en'),
            ReviewQuestionTranslation(review_questions[2].id, 'fr'),
            ReviewQuestionTranslation(review_questions[3].id, 'en'),
            ReviewQuestionTranslation(review_questions[3].id, 'fr'),
        ]
        db.session.add_all(review_question_translations)
        db.session.commit()

        self.add_email_template('reviews-assigned')

    def get_auth_header_for(self, email):
        body = {
            'email': email,
            'password': 'abc'
        }
        response = self.app.post('api/v1/authenticate', data=body)
        data = json.loads(response.data)
        header = {'Authorization': data['token']}
        return header

    def setup_one_reviewer_one_candidate(self, active=True):
        response = self.add_response(1, 5, is_submitted=True)

        answers = [
            Answer(1, 1, 'I will learn alot.'),
            Answer(1, 2, 'I will share by doing talks.')
        ]
        db.session.add_all(answers)
        db.session.commit()

        response_reviewers = [
            ResponseReviewer(1, 1) # assign reviewer 1 to candidate 1 response
        ]
        if not active:
            response_reviewers[0].deactivate()
        db.session.add_all(response_reviewers)
        db.session.commit()

    def test_one_reviewer_one_candidate(self):
        self.seed_static_data()
        self.setup_one_reviewer_one_candidate()
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1, 'language': 'en'}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 1)

    def test_one_reviewer_one_candidate_inactive(self):
        self.seed_static_data()
        self.setup_one_reviewer_one_candidate(active=False)
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1, 'language': 'en'}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 0)
        self.assertEqual(data['response']['id'], 0)

    @parameterized.expand([
        (True,), (False,)
    ])
    def test_one_reviewer_one_candidate_review_summary(self, active):
        self.seed_static_data()
        self.setup_one_reviewer_one_candidate(active=active)
        header = self.get_auth_header_for('ea@ea.com')
        params = {'event_id': 1}

        response = self.app.get('/api/v1/reviewassignment/summary', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_unallocated'], 2)  

    def setup_responses_and_no_reviewers(self):
        response = self.add_response(1, 5, is_submitted=True)

        answers = [
            Answer(1, 1, 'I will learn alot.'),
            Answer(1, 2, 'I will share by doing talks.')
        ]
        db.session.add_all(answers)
        db.session.commit()

    def test_no_response_reviewers(self):
        self.seed_static_data()
        self.setup_responses_and_no_reviewers()
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1, 'language': 'en'}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 0)
        
    def test_no_response_reviewers_reviews_unallocated(self):
        self.seed_static_data()
        self.setup_responses_and_no_reviewers()
        header = self.get_auth_header_for('ea@ea.com')
        params = {'event_id': 1}        
        response = self.app.get('/api/v1/reviewassignment/summary', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_unallocated'], 3)
        
    def setup_one_reviewer_three_candidates(self):
        self.add_response(application_form_id=1, user_id=5, is_submitted=True)
        self.add_response(application_form_id=1, user_id=6, is_submitted=True)
        self.add_response(application_form_id=1, user_id=7, is_submitted=True)

        answers = [
            Answer(1, 1, 'I will learn alot.'),
            Answer(1, 2, 'I will share by doing talks.'),
            Answer(2, 1, 'I want to do a PhD.'),
            Answer(2, 2, 'I will share by writing a blog.'),
            Answer(3, 1, 'I want to solve new problems.'),
            Answer(3, 2, 'I will share by tutoring.'),
        ]
        db.session.add_all(answers)
        db.session.commit()

        response_reviewers = [
            ResponseReviewer(1, 1),
            ResponseReviewer(2, 1),
            ResponseReviewer(3, 1)
        ]
        response_reviewers[1].deactivate()

        db.session.add_all(response_reviewers)
        db.session.commit()

    def test_one_reviewer_three_candidates(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates()
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1, 'language': 'en'}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 2)

    def setup_one_reviewer_three_candidates_and_one_completed_review(self):
        self.add_response(1, 5, is_submitted=True)
        self.add_response(1, 6, is_submitted=True)
        self.add_response(1, 7, is_submitted=True)

        answers = [
            Answer(1, 1, 'I will learn alot.'),
            Answer(1, 2, 'I will share by doing talks.'),
            Answer(2, 1, 'I want to do a PhD.'),
            Answer(2, 2, 'I will share by writing a blog.'),
            Answer(3, 1, 'I want to solve new problems.'),
            Answer(3, 2, 'I will share by tutoring.')
        ]
        db.session.add_all(answers)
        db.session.commit()

        response_reviewers = [
            ResponseReviewer(1, 1),
            ResponseReviewer(2, 1),
            ResponseReviewer(3, 1)
        ]
        db.session.add_all(response_reviewers)
        db.session.commit()

        review_response = ReviewResponse(1, 1, 1, 'en')
        review_response.submit()
        db.session.add(review_response)
        db.session.commit()

    def test_one_reviewer_three_candidates_and_one_completed_review(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates_and_one_completed_review()
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1, 'language': 'en'}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 2)

    def setup_one_reviewer_three_candidates_with_one_withdrawn_response_and_one_unsubmitted_response(self):
        withdrawn_response = self.add_response(1, 5, is_withdrawn=True)
        submitted_response = self.add_response(1, 7, is_submitted=True)
        self.add_response(1, 6)

        answers = [
            Answer(1, 1, 'I will learn alot.'),
            Answer(1, 2, 'I will share by doing talks.'),
            Answer(2, 1, 'I want to do a PhD.'),
            Answer(2, 2, 'I will share by writing a blog.'),
            Answer(3, 1, 'I want to solve new problems.'),
            Answer(3, 2, 'I will share by tutoring.')
        ]
        db.session.add_all(answers)
        db.session.commit()

        response_reviewers = [
            ResponseReviewer(1, 1),
            ResponseReviewer(2, 1),
            ResponseReviewer(3, 1)
        ]
        db.session.add_all(response_reviewers)
        db.session.commit()

    def test_one_reviewer_three_candidates_with_one_withdrawn_response_and_one_unsubmitted_response(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates_with_one_withdrawn_response_and_one_unsubmitted_response()
        header = self.get_auth_header_for('r1@r.com')
        params = {'event_id': 1, 'language': 'en'}

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 1)

    def setup_multiple_reviewers_with_different_subsets_of_candidates_and_reviews_completed(self):
        self.add_response(1, 5, is_submitted=True)
        self.add_response(1, 6, is_submitted=True)
        self.add_response(1, 7, is_submitted=True)
        self.add_response(1, 8, is_submitted=True)

        answers = [
            Answer(1, 1, 'I will learn alot.'),
            Answer(1, 2, 'I will share by doing talks.'),
            Answer(2, 1, 'I want to do a PhD.'),
            Answer(2, 2, 'I will share by writing a blog.'),
            Answer(3, 1, 'I want to solve new problems.'),
            Answer(3, 2, 'I will share by tutoring.'),
            Answer(4, 1, 'I want to exchange ideas with like minded people'),
            Answer(4, 2, 'I will mentor people interested in ML.')
        ]
        db.session.add_all(answers)
        db.session.commit()

        response_reviewers = [
            ResponseReviewer(1, 1),
            ResponseReviewer(2, 1),
            ResponseReviewer(3, 1),

            ResponseReviewer(2, 2),
            ResponseReviewer(3, 2),

            ResponseReviewer(1, 3),
            ResponseReviewer(2, 3),
            ResponseReviewer(3, 3),
            ResponseReviewer(4, 3),

            ResponseReviewer(1, 4),
            ResponseReviewer(2, 4)
        ]
        response_reviewers[-1].deactivate()
        db.session.add_all(response_reviewers)
        db.session.commit()

        review_responses = [
            ReviewResponse(1, 2, 2, 'en'),
            ReviewResponse(1, 3, 1, 'en'),
            ReviewResponse(1, 3, 2, 'en'),
            ReviewResponse(1, 4, 1, 'en')
        ]
        for rr in review_responses:
            rr.submit()

        db.session.add_all(review_responses)
        db.session.commit()
    
    def test_multiple_reviewers_with_different_subsets_of_candidates_and_reviews_completed(self):
        self.seed_static_data()
        self.setup_multiple_reviewers_with_different_subsets_of_candidates_and_reviews_completed()
        params = {'event_id': 1, 'language': 'en'}

        header = self.get_auth_header_for('r1@r.com')
        response1 = self.app.get('/api/v1/review', headers=header, data=params)
        data1 = json.loads(response1.data)
        header = self.get_auth_header_for('r2@r.com')
        response2 = self.app.get('/api/v1/review', headers=header, data=params)
        data2 = json.loads(response2.data)
        header = self.get_auth_header_for('r3@r.com')
        response3 = self.app.get('/api/v1/review', headers=header, data=params)
        data3 = json.loads(response3.data)
        header = self.get_auth_header_for('r4@r.com')
        response4 = self.app.get('/api/v1/review', headers=header, data=params)
        data4 = json.loads(response4.data)

        self.assertEqual(data1['reviews_remaining_count'], 3)
        self.assertEqual(data2['reviews_remaining_count'], 1)
        self.assertEqual(data3['reviews_remaining_count'], 2)
        self.assertEqual(data4['reviews_remaining_count'], 0)

    def test_skipping(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates()
        params = {'event_id': 1, 'skip': 1, 'language': 'en'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['response']['user_id'], 7)
        self.assertEqual(data['response']['answers'][0]['value'], 'I want to solve new problems.')

    def test_high_skip_defaults_to_last_review(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates()
        params = {'event_id': 1, 'skip': 5, 'language': 'en'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['response']['user_id'], 7)
        self.assertEqual(data['response']['answers'][1]['value'], 'I will share by tutoring.')

    def setup_candidate_who_has_applied_to_multiple_events(self):
        user_id = 5
        
        self.add_response(application_form_id=1, user_id=user_id, is_submitted=True)
        self.add_response(application_form_id=2, user_id=user_id, is_submitted=True)

        answers = [
            Answer(1, 1, 'I will learn alot.'),
            Answer(1, 2, 'I will share by doing talks.'),
            Answer(2, 3, 'Yes I worked on a vision task.'),
            Answer(2, 4, 'Yes I want the travel award.')
        ]
        db.session.add_all(answers)
        db.session.commit()

        response_reviewers = [
            ResponseReviewer(1, 1),
            ResponseReviewer(2, 1)
        ]
        db.session.add_all(response_reviewers)
        db.session.commit()

    def test_filtering_on_event_when_candidate_has_applied_to_more_than(self):
        self.seed_static_data()
        self.setup_candidate_who_has_applied_to_multiple_events()
        params = {'event_id': 2, 'language': 'en'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews_remaining_count'], 1)
        self.assertEqual(data['response']['user_id'], 5)
        self.assertEqual(data['response']['answers'][0]['value'], 'Yes I worked on a vision task.')

    def setup_multi_choice_answer(self):
        self.add_response(1, 5, is_submitted=True)

        answer = Answer(1, 5, 'indaba-2017')
        db.session.add(answer)
        db.session.commit()

        response_reviewer = ResponseReviewer(1, 1)
        db.session.add(response_reviewer)
        db.session.commit()
    
    def test_multi_choice_answers_use_label_instead_of_value(self):
        self.seed_static_data()
        self.setup_multi_choice_answer()
        params = {'event_id': 1, 'language': 'en'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/review', headers=header, data=params)
        data = json.loads(response.data)
        print(data)

        self.assertEqual(data['response']['answers'][0]['value'], 'Yes, I attended the 2017 Indaba')

    def test_review_response_not_found(self):
        self.seed_static_data()
        params = {'id': 55, 'language': 'en'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/reviewresponse', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, REVIEW_RESPONSE_NOT_FOUND[1])

    def setup_review_response(self):
        self.add_response(1, 5, is_submitted=True)

        answer = Answer(1, 1, 'To learn alot')
        db.session.add(answer)
        db.session.commit()

        self.review_response = ReviewResponse(1, 1, 1, 'en')
        self.review_response.review_scores.append(ReviewScore(1, 'answer1'))
        self.review_response.review_scores.append(ReviewScore(2, 'answer2'))
        db.session.add(self.review_response)
        db.session.commit()

        db.session.flush()
        

    def test_review_response(self):
        self.seed_static_data()
        self.setup_review_response()
        params = {'id': self.review_response.id, 'language': 'en'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/reviewresponse', headers=header, data=params)
        data = json.loads(response.data)

        print(data)

        self.assertEqual(data['review_form']['id'], 1)
        self.assertEqual(data['review_response']['reviewer_user_id'], 1)
        self.assertEqual(data['review_response']['response_id'], 1)
        self.assertEqual(data['review_response']['scores'][0]['value'], 'answer1')
        self.assertEqual(data['review_response']['scores'][1]['value'], 'answer2')

    def test_prevent_saving_review_response_reviewer_was_not_assigned_to_response(self):
        self.seed_static_data()
        params = json.dumps({'review_form_id': 1, 'response_id': 1, 'scores': [{'review_question_id': 1, 'value': 'test_answer'}], 'language': 'en', 'is_submitted': False})
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.post('/api/v1/reviewresponse', headers=header, data=params, content_type='application/json')

        self.assertEqual(response.status_code, FORBIDDEN[1])

    def test_can_still_submit_inactive_response_reviewer(self):
        self.seed_static_data()
        self.setup_one_reviewer_three_candidates()
        params = json.dumps({'review_form_id': 1, 'response_id': 2, 'scores': [{'review_question_id': 1, 'value': 'test_answer'}], 'language': 'en', 'is_submitted': True})
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.post('/api/v1/reviewresponse', headers=header, data=params, content_type='application/json')

        self.assertEqual(response.status_code, 201)

    def setup_response_reviewer(self):
        self.add_response(1, 5, is_submitted=True)

        response_reviewer = ResponseReviewer(1, 1)
        db.session.add(response_reviewer)
        db.session.commit()

    def test_saving_review_response(self):
        self.seed_static_data()
        self.setup_response_reviewer()
        params = json.dumps({'review_form_id': 1, 'response_id': 1, 'scores': [{'review_question_id': 1, 'value': 'test_answer'}], 'language': 'en', 'is_submitted': False})
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.post('/api/v1/reviewresponse', headers=header, data=params, content_type='application/json')

        review_scores = db.session.query(ReviewScore).filter_by(review_response_id=1).all()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(review_scores), 1)
        self.assertEqual(review_scores[0].value, 'test_answer')

    def setup_existing_review_response(self):
        self.add_response(1, 5, is_submitted=True)

        response_reviewer = ResponseReviewer(1, 1)
        db.session.add(response_reviewer)
        db.session.commit()

        review_response = ReviewResponse(1, 1, 1, 'en')
        review_response.submit()
        review_response.review_scores = [ReviewScore(1, 'test_answer1'), ReviewScore(2, 'test_answer2')]
        db.session.add(review_response)
        db.session.commit()

    def test_updating_review_response(self):
        self.seed_static_data()
        self.setup_existing_review_response()
        params = json.dumps({'review_form_id': 1, 'response_id': 1, 'scores': [{'review_question_id': 1, 'value': 'test_answer3'}, {'review_question_id': 2, 'value': 'test_answer4'}], 'language': 'en', 'is_submitted': True})
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.put('/api/v1/reviewresponse', headers=header, data=params, content_type='application/json')

        review_scores = db.session.query(ReviewScore).filter_by(review_response_id=1).order_by(ReviewScore.review_question_id).all()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(review_scores), 2)
        self.assertEqual(review_scores[0].value, 'test_answer3')
        self.assertEqual(review_scores[1].value, 'test_answer4')

    def test_user_cant_assign_responsesreviewer_without_system_or_event_admin_role(self):
        self.seed_static_data()
        params = {'event_id': 1, 'reviewer_user_email': 'r2@r.com', 'num_reviews': 10}
        header = self.get_auth_header_for('c1@c.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

        self.assertEqual(response.status_code, FORBIDDEN[1])

    def test_reviewer_not_found(self):
        self.seed_static_data()
        params = {'event_id': 1, 'reviewer_user_email': 'non_existent@user.com', 'num_reviews': 10}
        header = self.get_auth_header_for('sa@sa.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

        self.assertEqual(response.status_code, USER_NOT_FOUND[1])

    def test_add_reviewer_with_no_roles(self):
        self.seed_static_data()
        params = {'event_id': 1, 'reviewer_user_email': 'r1@r.com', 'num_reviews': 10}
        header = self.get_auth_header_for('ea@ea.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

        event_roles = db.session.query(EventRole).filter_by(user_id=1, event_id=1).all()
        self.assertEqual(len(event_roles), 1)
        self.assertEqual(event_roles[0].role, 'reviewer')

    def test_add_reviewer_with_a_role(self):
        self.seed_static_data()
        params = {'event_id': 1, 'reviewer_user_email': 'ea@ea.com', 'num_reviews': 10}
        header = self.get_auth_header_for('sa@sa.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

        event_roles = db.session.query(EventRole).filter_by(user_id=10, event_id=1).order_by(EventRole.id).all()
        self.assertEqual(len(event_roles), 2)
        self.assertEqual(event_roles[0].role, 'admin')
        self.assertEqual(event_roles[1].role, 'reviewer')

    def setup_responses_without_reviewers(self):
        self.add_response(1, 5, is_submitted=True)
        self.add_response(1, 6, is_submitted=True)
        self.add_response(1, 7, is_submitted=True)
        self.add_response(1, 8, is_submitted=True)

    def test_adding_first_reviewer(self):
        self.seed_static_data()
        self.setup_responses_without_reviewers()
        params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 4}
        header = self.get_auth_header_for('ea@ea.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)
        response_reviewers = db.session.query(ResponseReviewer).filter_by(reviewer_user_id=3).all()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response_reviewers), 4)
    
    def test_limit_of_num_reviews(self):
        self.seed_static_data()
        self.setup_responses_without_reviewers()
        params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
        header = self.get_auth_header_for('ea@ea.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

        response_reviewers = db.session.query(ResponseReviewer).filter_by(reviewer_user_id=3).all()
        self.assertEqual(len(response_reviewers), 3)

    def setup_reviewer_with_own_response(self):
        self.add_response(1, 3, is_submitted=True) # reviewer
        self.add_response(1, 5, is_submitted=True) # someone else

    def test_reviewer_does_not_get_assigned_to_own_response(self):
        self.seed_static_data()
        self.setup_reviewer_with_own_response()
        params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
        header = self.get_auth_header_for('ea@ea.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

        response_reviewers = db.session.query(ResponseReviewer).filter_by(reviewer_user_id=3).all()
        self.assertEqual(len(response_reviewers), 1)
        self.assertEqual(response_reviewers[0].response_id, 2)

    def setup_withdrawn_and_unsubmitted_responses(self):
        self.add_response(1, 5)
        self.add_response(1, 6, is_withdrawn=True)
        self.add_response(1, 7, is_submitted=True)

    def test_withdrawn_and_unsubmitted_responses_are_not_assigned_reviewers(self):
        self.seed_static_data()
        self.setup_withdrawn_and_unsubmitted_responses()
        params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
        header = self.get_auth_header_for('ea@ea.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

        response_reviewers = db.session.query(ResponseReviewer).filter_by(reviewer_user_id=3).all()
        self.assertEqual(len(response_reviewers), 1)
        self.assertEqual(response_reviewers[0].response_id, 3)

    def setup_response_with_three_reviewers(self):
        response = self.add_response(1, 5, is_submitted=True)

        response_reviewers = [
            ResponseReviewer(1, 1),
            ResponseReviewer(1, 2),
            ResponseReviewer(1, 4)
        ]
        db.session.add_all(response_reviewers)
        db.session.commit()

    def test_response_with_three_reviewers_does_not_get_assigned_another_reviewer(self):
        self.seed_static_data()
        self.setup_response_with_three_reviewers()
        params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
        header = self.get_auth_header_for('ea@ea.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)

        response_reviewers = db.session.query(ResponseReviewer).filter_by(reviewer_user_id=3).all()
        self.assertEqual(len(response_reviewers), 0)   

    def setup_responsereview_with_different_reviewer(self):
        self.add_response(1, 5, is_submitted=True)

        response_reviewer = ResponseReviewer(1, 1)
        db.session.add(response_reviewer)
        db.session.commit()
        
    def test_response_will_get_multiple_reviewers_assigned(self):
        self.seed_static_data()
        self.setup_responsereview_with_different_reviewer()
        params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
        header = self.get_auth_header_for('ea@ea.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)
        response_reviewers = db.session.query(ResponseReviewer).order_by(ResponseReviewer.reviewer_user_id).all()

        self.assertEqual(len(response_reviewers), 2)
        self.assertEqual(response_reviewers[0].reviewer_user_id, 1)
        self.assertEqual(response_reviewers[1].reviewer_user_id, 3)
    
    def setup_reviewer_is_not_assigned_to_response_more_than_once(self):
        self.add_response(1, 5, is_submitted=True)

    def setup_count_reviews_allocated_and_completed(self):
        db.session.add_all([ 
            EventRole('reviewer', 1, 1),
            EventRole('reviewer', 2, 1),
            EventRole('reviewer', 3, 1),
            EventRole('reviewer', 4, 1)
        ])
        
        self.add_response(1, 5, is_submitted=True) #1
        self.add_response(1, 6, is_submitted=True) #2
        self.add_response(1, 7, is_submitted=True) #3
        self.add_response(1, 8, is_submitted=True) #4
        self.add_response(2, 5, is_submitted=True) #5
        self.add_response(2, 6, is_submitted=True)  #6

        response_reviewers = [
            ResponseReviewer(1, 2),
            ResponseReviewer(2, 2),
            ResponseReviewer(3, 2),
            ResponseReviewer(4, 2),
            ResponseReviewer(6, 2),

            ResponseReviewer(2, 3),
            ResponseReviewer(4, 3),

            ResponseReviewer(3, 4),

            ResponseReviewer(5, 1),

        ]


        db.session.add_all(response_reviewers)
        # review form, review_user_id, response_id 
        review_responses = [
            ReviewResponse(1, 3, 2, 'en'), 
            ReviewResponse(1, 3, 4, 'en'),
            ReviewResponse(1, 2, 1, 'en'),
            ReviewResponse(1, 2, 3, 'en'),
            ReviewResponse(1, 2, 4, 'en'),
            ReviewResponse(2, 1, 5, 'en'),
            ReviewResponse(2, 2, 6, 'en')
        ]
        db.session.add_all(review_responses)

        db.session.commit()

        # response 1 - 1 review assigned - 1 complete
        # response 2 - 2 reviews - 1 complete
        # response 3 - 2 reviews - 1 complete
        # response 4 - 2 reviews - 1 complete
        # response 5 - 1 review - 1 complete
        # response 6 - 1 review - 1 complete

        # reviewer 1 - 1 review assigned (1 from event 2) - 1 complete
        # reviewer 2 - 5 reviews assigned (1 from event 2)- 3 complete
        # reviewer 3 - 2 reviews assigned - 2 complete
        # reviewer 4 - 1 review assigned - none complete 
        
        # total assigned reviews: 9
        # total required review = 6*3 = 18
        # total unallocated: 18 - 9 = 9
        # total completed reviews: 6        

    @SkipTest
    def test_count_reviews_allocated_and_completed(self):
        self.seed_static_data()
        self.setup_count_reviews_allocated_and_completed()
        header = self.get_auth_header_for('ea@ea.com')
        params = {'event_id': 1}

        response = self.app.get('/api/v1/reviewassignment', headers=header, data=params)
        
        data = json.loads(response.data)
        data = sorted(data, key=lambda k: k['email'])
        LOGGER.debug(data)
        self.assertEqual(len(data),3)
        self.assertEqual(data[0]['email'], 'r2@r.com')
        self.assertEqual(data[0]['reviews_allocated'], 4)
        self.assertEqual(data[0]['reviews_completed'], 3)
        self.assertEqual(data[1]['email'], 'r3@r.com')
        self.assertEqual(data[1]['reviews_allocated'], 2)
        self.assertEqual(data[1]['reviews_completed'], 2)
        self.assertEqual(data[2]['email'], 'r4@r.com')
        self.assertEqual(data[2]['reviews_allocated'], 1)
        self.assertEqual(data[2]['reviews_completed'], 0)

    def test_reviewer_is_not_assigned_to_response_more_than_once(self):
        self.seed_static_data()
        self.setup_reviewer_is_not_assigned_to_response_more_than_once()
        params = {'event_id': 1, 'reviewer_user_email': 'r3@r.com', 'num_reviews': 3}
        header = self.get_auth_header_for('ea@ea.com')

        response = self.app.post('/api/v1/reviewassignment', headers=header, data=params)
        response2 = self.app.post('/api/v1/reviewassignment', headers=header, data=params)
        response_reviewers = db.session.query(ResponseReviewer).all()

        self.assertEqual(len(response_reviewers), 1)

    def setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores(self):
        second_reviewer = EventRole('reviewer', 2, 1)
        db.session.add(second_reviewer)
        db.session.commit()

        users_id = [5,6,7]
        self.add_response(application_form_id=1, user_id=users_id[0], is_submitted=True)
        self.add_response(application_form_id=1, user_id=users_id[1], is_submitted=True)
        self.add_response(application_form_id=1, user_id=users_id[2], is_submitted=True)
        
        final_verdict_options = [
            {'label': 'Yes', 'value': 2},
            {'label': 'No', 'value': 0},
            {'label': 'Maybe', 'value': 1},
        ]
        verdict_question = ReviewQuestion(1, None, 'multi-choice', True, 3, 0)
        db.session.add(verdict_question)
        db.session.commit()
        verdict_question_translation = ReviewQuestionTranslation(verdict_question.id, 'en', headline='Final Verdict', options=final_verdict_options)
        db.session.add(verdict_question_translation)
        db.session.commit()

        review_responses = [
            ReviewResponse(1,3,1, 'en'), 
            ReviewResponse(1,3,2, 'en'),
            ReviewResponse(1,2,1, 'en'), 
            ReviewResponse(1,2,2, 'en'),
            ReviewResponse(1,3,3, 'en')
        ]
        review_responses[0].review_scores = [ReviewScore(1, '23'), ReviewScore(5, '1')]
        review_responses[1].review_scores = [ReviewScore(1, '55'), ReviewScore(5, '2')]
        review_responses[2].review_scores = [ReviewScore(1, '45'), ReviewScore(2, '67'), ReviewScore(5, 'No')]
        review_responses[3].review_scores = [ReviewScore(1, '220'), ReviewScore(5, '2')]
        review_responses[4].review_scores = [ReviewScore(1, '221'), ReviewScore(5, '1')]
        db.session.add_all(review_responses)
        db.session.commit()

        return users_id


    def test_review_history_returned(self):
        self.seed_static_data()
        users_id = self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(len(data['reviews']), 3)
        self.assertEqual(data['num_entries'], 3)

        self.assertEqual(data['reviews'][0]['review_response_id'], 1)
        self.assertEqual(data['reviews'][0]['reviewed_user_id'], str(users_id[0]))

        self.assertEqual(data['reviews'][1]['review_response_id'], 2)
        self.assertEqual(data['reviews'][1]['reviewed_user_id'], str(users_id[1]))

        self.assertEqual(data['reviews'][2]['review_response_id'], 5)
        self.assertEqual(data['reviews'][2]['reviewed_user_id'], str(users_id[2]))
        
    def test_brings_back_only_logged_in_reviewer_reviewresponses(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r2@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(len(data['reviews']), 2)
        self.assertEqual(data['reviews'][0]['review_response_id'], 3)
        self.assertEqual(data['reviews'][1]['review_response_id'], 4)

    def test_logged_in_user_not_reviewer(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('c1@c.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)

        self.assertEqual(response.status_code, FORBIDDEN[1])

    def setup_reviewer_with_no_reviewresponses(self):
        reviewer = EventRole('reviewer', 1, 1)
        db.session.add(reviewer)
        db.session.commit()

    def test_reviewer_with_no_reviewresponses(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()
        self.setup_reviewer_with_no_reviewresponses()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)  
        data = json.loads(response.data)

        self.assertEqual(data['num_entries'], 0)
        self.assertEqual(data['reviews'], [])  

    def test_order_by_reviewresponseid(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)
    
        self.assertEqual(data['reviews'][0]['review_response_id'], 1)
        self.assertEqual(data['reviews'][1]['review_response_id'], 2)
        self.assertEqual(data['reviews'][2]['review_response_id'], 5)

    def setup_reviewresponses_with_unordered_timestamps(self):
        final_verdict_options = [
            {'label': 'Yes', 'value': 2},
            {'label': 'No', 'value': 0},
            {'label': 'Maybe', 'value': 1},
        ]

        verdict_question = ReviewQuestion(1, None, 'multi-choice', True, 3, 0)
        db.session.add(verdict_question)
        db.session.commit()
        verdict_question_translation = ReviewQuestionTranslation(verdict_question.id, 'en', headline='Final Verdict', options=final_verdict_options)
        db.session.add(verdict_question_translation)
        db.session.commit()

        self.add_response(1, 5, is_submitted=True)
        self.add_response(1, 6, is_submitted=True)
        self.add_response(1, 7, is_submitted=True)

        review_response_1 = ReviewResponse(1,3,1, 'en')
        review_response_2 = ReviewResponse(1,3,2, 'en')
        review_response_3 = ReviewResponse(1,3,3, 'en')
        review_response_1.submitted_timestamp = datetime(2019, 1, 1)
        review_response_2.submitted_timestamp = datetime(2018, 1, 1)
        review_response_3.submitted_timestamp = datetime(2018, 6, 6)
        review_responses = [review_response_1, review_response_2, review_response_3]
        review_responses[0].review_scores = [ReviewScore(1, '67'), ReviewScore(5, 'Yes')] 
        review_responses[1].review_scores = [ReviewScore(1, '23'), ReviewScore(5, 'Yes')]
        review_responses[2].review_scores = [ReviewScore(1, '53'), ReviewScore(5, 'Yes')]
        db.session.add_all(review_responses)
        db.session.commit()

    def test_order_by_submittedtimestamp(self):
        self.seed_static_data()
        self.setup_reviewresponses_with_unordered_timestamps()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'submitted_timestamp'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)
        LOGGER.debug(data)
        self.assertEqual(data['reviews'][0]['submitted_timestamp'], '2018-01-01T00:00:00')
        self.assertEqual(data['reviews'][1]['submitted_timestamp'], '2018-06-06T00:00:00')
        self.assertEqual(data['reviews'][2]['submitted_timestamp'], '2019-01-01T00:00:00')

    # TODO re-add these tests once we can get the info outside of AppUser
    @SkipTest
    def test_order_by_nationalitycountry(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'nationality_country'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)
    
        self.assertEqual(data['reviews'][0]['nationality_country'], 'Botswana')
        self.assertEqual(data['reviews'][1]['nationality_country'], 'South Africa')
        self.assertEqual(data['reviews'][2]['nationality_country'], 'Zimbabwe')

    # TODO re-add these tests once we can get the info outside of AppUser
    @SkipTest
    def test_order_by_residencecountry(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'residence_country'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)
    
        self.assertEqual(data['reviews'][0]['residence_country'], 'Egypt')
        self.assertEqual(data['reviews'][1]['residence_country'], 'Mozambique')
        self.assertEqual(data['reviews'][2]['residence_country'], 'Namibia')

    # TODO re-add these tests once we can get the info outside of AppUser
    @SkipTest
    def test_order_by_affiliation(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'affiliation'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)
    
        self.assertEqual(data['reviews'][0]['affiliation'], 'RU')
        self.assertEqual(data['reviews'][1]['affiliation'], 'UFH')
        self.assertEqual(data['reviews'][2]['affiliation'], 'UWC')

    # TODO re-add these tests once we can get the info outside of AppUser
    @SkipTest
    def test_order_by_department(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'department'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews'][0]['department'], 'CS') # ascii ordering orders capital letters before lowercase
        self.assertEqual(data['reviews'][1]['department'], 'Chem')
        self.assertEqual(data['reviews'][2]['department'], 'Phys')       

    @SkipTest
    def test_order_by_usercategory(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 10, 'sort_column' : 'user_category'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)
        data = json.loads(response.data)

        self.assertEqual(data['reviews'][0]['user_category'], 'Honours')
        self.assertEqual(data['reviews'][1]['user_category'], 'MSc')
        self.assertEqual(data['reviews'][2]['user_category'], 'Student')

    def setup_two_extra_responses_for_reviewer3(self):
        self.add_response(1, 8, is_submitted=True)
        self.add_response(1, 1, is_submitted=True)

        review_responses = [
            ReviewResponse(1,3,4, 'en'),
            ReviewResponse(1,3,5, 'en')
        ]
        review_responses[0].review_scores = [ReviewScore(1, '89'), ReviewScore(5, 'Maybe')] 
        review_responses[1].review_scores = [ReviewScore(1, '75'), ReviewScore(5, 'Yes')]
        db.session.add_all(review_responses)
        db.session.commit()

    def test_first_page_in_pagination(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()
        self.setup_two_extra_responses_for_reviewer3()

        params ={'event_id' : 1, 'page_number' : 0, 'limit' : 2, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)  
        data = json.loads(response.data)

        self.assertEqual(len(data['reviews']), 2)
        self.assertEqual(data['num_entries'], 5)

        self.assertEqual(data['reviews'][0]['review_response_id'], 1)
        self.assertEqual(data['reviews'][1]['review_response_id'], 2)

    def test_middle_page_in_pagination(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()
        self.setup_two_extra_responses_for_reviewer3()

        params ={'event_id' : 1, 'page_number' : 1, 'limit' : 2, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)  
        data = json.loads(response.data)

        self.assertEqual(len(data['reviews']), 2)
        self.assertEqual(data['num_entries'], 5)

        self.assertEqual(data['reviews'][0]['review_response_id'], 5)
        self.assertEqual(data['reviews'][1]['review_response_id'], 6)

    def test_last_page_in_pagination(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()
        self.setup_two_extra_responses_for_reviewer3()

        params ={'event_id' : 1, 'page_number' : 2, 'limit' : 2, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)  
        data = json.loads(response.data)

        self.assertEqual(len(data['reviews']), 1)
        self.assertEqual(data['num_entries'], 5)
        self.assertEqual(data['reviews'][0]['review_response_id'], 7)

    def test_total_number_of_pages_greater_than_zero(self):
        self.seed_static_data()
        self.setup_reviewer_responses_finalverdict_reviewquestion_reviewresponses_and_scores()
        self.setup_two_extra_responses_for_reviewer3()

        params ={'event_id' : 1, 'page_number' : 2, 'limit' : 2, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r3@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)  
        data = json.loads(response.data)

        self.assertEqual(data['total_pages'], 3)

    def test_total_number_of_pages_when_zero(self):
        self.seed_static_data()
        self.setup_reviewer_with_no_reviewresponses()

        params ={'event_id' : 1, 'page_number' : 2, 'limit' : 2, 'sort_column' : 'review_response_id'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/reviewhistory', headers=header, data=params)  
        data = json.loads(response.data)

        self.assertEqual(data['total_pages'], 0)
    
    def test_review_form_language(self):
        """Test that the review form questions are returned in the correct language."""
        self.seed_static_data()
        params ={'event_id' : 1, 'language': 'en'}
        header = self.get_auth_header_for('r1@r.com')

        response = self.app.get('/api/v1/review', headers=header, data=params)  
        data = json.loads(response.data)

        self.assertEqual(data['review_form']['review_questions'][1]['description'], 'English Description')
        self.assertEqual(data['review_form']['review_questions'][1]['headline'], 'English Headline')
        self.assertEqual(data['review_form']['review_questions'][1]['placeholder'], 'English Placeholder')
        self.assertDictEqual(data['review_form']['review_questions'][1]['options'][0], {'label': 'en1', 'value': 'en'})
        self.assertEqual(data['review_form']['review_questions'][1]['validation_regex'], 'EN Regex')        
        self.assertEqual(data['review_form']['review_questions'][1]['validation_text'], 'EN Validation Message')
        
        params ={'event_id' : 1, 'language': 'fr'}

        response = self.app.get('/api/v1/review', headers=header, data=params)  
        data = json.loads(response.data)

        self.assertEqual(data['review_form']['review_questions'][1]['description'], 'French Description')
        self.assertEqual(data['review_form']['review_questions'][1]['headline'], 'French Headline')
        self.assertEqual(data['review_form']['review_questions'][1]['placeholder'], 'French Placeholder')
        self.assertDictEqual(data['review_form']['review_questions'][1]['options'][0], {'label': 'fr1', 'value': 'fr'})
        self.assertEqual(data['review_form']['review_questions'][1]['validation_regex'], 'FR Regex')        
        self.assertEqual(data['review_form']['review_questions'][1]['validation_text'], 'FR Validation Message')


class ReviewListAPITest(ApiTestCase):

    def seed_static_data(self):
        self.event1 = self.add_event(key='event1')
        self.event2 = self.add_event(key='event2')

        self.reviewer1 = self.add_user('reviewer1@mail.com')
        self.reviewer2 = self.add_user('reviewer2@mail.com')
        self.event1.add_event_role('reviewer', self.reviewer1.id)
        self.event2.add_event_role('reviewer', self.reviewer1.id)
        self.event1.add_event_role('reviewer', self.reviewer2.id)
        self.event2.add_event_role('reviewer', self.reviewer2.id)

        self.user1 = self.add_user('user1@mail.com')
        user2 = self.add_user('user2@mail.com')
        user3 = self.add_user('user3@mail.com')
        user4 = self.add_user('user4@mail.com')

        application_form1 = self.create_application_form(self.event1.id)
        section1 = self.add_section(application_form1.id)
        question1 = self.add_question(application_form1.id, section1.id)
        question1.key = 'review-identifier'
        self.add_question_translation(question1.id, 'en', 'Headline 1 EN')
        self.add_question_translation(question1.id, 'fr', 'Headline 1 FR')
        question2 = self.add_question(application_form1.id, section1.id)
        question2.key = 'review-identifier'
        self.add_question_translation(question2.id, 'en', 'Headline 2 EN')
        self.add_question_translation(question2.id, 'fr', 'Headline 2 FR')
        question3 = self.add_question(application_form1.id, section1.id)
        self.add_question_translation(question3.id, 'en', 'Headline 3 EN')
        self.add_question_translation(question3.id, 'fr', 'Headline 3 FR')

        review_form1 = self.add_review_form(application_form1.id)
        review_q1 = self.add_review_question(review_form1.id, weight=1)
        review_q2 = self.add_review_question(review_form1.id, weight=0)
        review_q3 = self.add_review_question(review_form1.id, weight=1)

        application_form2 = self.create_application_form(self.event2.id)
        review_form2 = self.add_review_form(application_form2.id)

        event1_response1 = self.add_response(application_form1.id, self.user1.id, is_submitted=True)
        self.add_answer(event1_response1.id, question1.id, 'First answer')
        self.add_answer(event1_response1.id, question2.id, 'Second answer')
        self.add_answer(event1_response1.id, question3.id, 'Third answer')

        event1_response2 = self.add_response(application_form1.id, user2.id, is_submitted=True, language='fr')
        self.add_answer(event1_response2.id, question1.id, 'Forth answer')
        self.add_answer(event1_response2.id, question2.id, 'Fifth answer')
        self.add_answer(event1_response2.id, question3.id, 'Sixth answer')

        event1_response3 = self.add_response(application_form1.id, user3.id, is_submitted=True)
        self.add_answer(event1_response3.id, question1.id, 'Seventh answer')
        self.add_answer(event1_response3.id, question2.id, 'Eigth answer')
        self.add_answer(event1_response3.id, question3.id, 'Ninth answer')

        event1_response4 = self.add_response(application_form1.id, user4.id, is_submitted=True, language='zu')
        self.add_answer(event1_response4.id, question1.id, 'Tenth answer')
        self.add_answer(event1_response4.id, question2.id, 'Eleventh answer')
        self.add_answer(event1_response4.id, question3.id, 'Twelfth answer')

        event2_response1 = self.add_response(application_form2.id, self.user1.id, is_submitted=True)
        event2_response2 = self.add_response(application_form2.id, user2.id, is_submitted=True, language='fr')
        event2_response3 = self.add_response(application_form2.id, user3.id, is_submitted=True)

        # Review 1 completed review
        self.add_response_reviewer(event1_response1.id, self.reviewer1.id)
        review_response1 = self.add_review_response(self.reviewer1.id, event1_response1.id, review_form1.id)
        review_response1.submit()
        self.add_review_score(review_response1.id, review_q1.id, 10.5)
        self.add_review_score(review_response1.id, review_q2.id, 100)
        self.add_review_score(review_response1.id, review_q3.id, 'Hello world')

        # Reviewer 1 incomplete review
        self.review_response1_submitted = review_response1.submitted_timestamp.isoformat()
        self.add_response_reviewer(event1_response2.id, self.reviewer1.id)
        review_response2 = self.add_review_response(self.reviewer1.id, event1_response2.id, review_form1.id)
        self.add_review_score(review_response2.id, review_q1.id, 13)

        # Reviewer 1 not started review
        self.add_response_reviewer(event1_response3.id, self.reviewer1.id)

        # Confounders
        self.add_response_reviewer(event1_response2.id, self.reviewer2.id)
        self.add_response_reviewer(event1_response3.id, self.reviewer2.id)
        self.add_response_reviewer(event2_response1.id, self.reviewer1.id)
        self.add_response_reviewer(event2_response2.id, self.reviewer2.id)

    def test_review_list(self):
        self.seed_static_data()
        params ={'event_id' : 1, 'language': 'en'}

        response = self.app.get(
            '/api/v1/reviewlist', 
            headers=self.get_auth_header_for('reviewer1@mail.com'), 
            data=params)  

        data = json.loads(response.data)

        self.assertEqual(len(data), 3)

        self.assertEqual(data[0]['response_id'], 1)
        self.assertEqual(data[0]['language'], 'en')
        self.assertEqual(len(data[0]['information']), 2)
        self.assertEqual(data[0]['information'][0]['headline'], 'Headline 1 EN')
        self.assertEqual(data[0]['information'][0]['value'], 'First answer')
        self.assertEqual(data[0]['information'][1]['headline'], 'Headline 2 EN')
        self.assertEqual(data[0]['information'][1]['value'], 'Second answer')
        self.assertTrue(data[0]['started'])
        self.assertEqual(data[0]['submitted'], self.review_response1_submitted)
        self.assertEqual(data[0]['total_score'], 10.5)

        self.assertEqual(data[1]['response_id'], 2)
        self.assertEqual(data[1]['language'], 'fr')
        self.assertEqual(len(data[1]['information']), 2)
        self.assertEqual(data[1]['information'][0]['headline'], 'Headline 1 EN')
        self.assertEqual(data[1]['information'][0]['value'], 'Forth answer')
        self.assertEqual(data[1]['information'][1]['headline'], 'Headline 2 EN')
        self.assertEqual(data[1]['information'][1]['value'], 'Fifth answer')
        self.assertTrue(data[1]['started'])
        self.assertIsNone(data[1]['submitted'])
        self.assertEqual(data[1]['total_score'], 13)

        self.assertEqual(data[2]['response_id'], 3)
        self.assertEqual(data[2]['language'], 'en')
        self.assertEqual(len(data[2]['information']), 2)
        self.assertEqual(data[2]['information'][0]['headline'], 'Headline 1 EN')
        self.assertEqual(data[2]['information'][0]['value'], 'Seventh answer')
        self.assertEqual(data[2]['information'][1]['headline'], 'Headline 2 EN')
        self.assertEqual(data[2]['information'][1]['value'], 'Eigth answer')
        self.assertFalse(data[2]['started'])
        self.assertIsNone(data[2]['submitted'])
        self.assertEqual(data[2]['total_score'], 0.0)

class ResponseReviewerAssignmentApiTest(ApiTestCase):
    def seed_static_data(self):
        self.event = self.add_event(key='event1')
        self.event2 = self.add_event(key='event2')
        self.event_admin = self.add_user('eventadmin@mail.com')
        self.reviewer = self.add_user('reviewer@mail.com')
        self.reviewer_user_id = self.reviewer.id

        self.user1 = self.add_user('user1@mail.com')
        self.user2 = self.add_user('user2@mail.com')
        self.user3 = self.add_user('user3@mail.com')

        self.event.add_event_role('admin', self.event_admin.id)
        
        application_form = self.create_application_form(self.event.id)
        application_form2 = self.create_application_form(self.event2.id)
        self.response1 = self.add_response(application_form.id, self.user1.id, is_submitted=True)
        self.response2 = self.add_response(application_form.id, self.user2.id, is_submitted=True)
        self.response3 = self.add_response(application_form.id, self.user3.id, is_submitted=True)

        self.add_review_form(application_form.id)
        self.add_review_form(application_form2.id)

        self.event2_response_id = self.add_response(application_form2.id, self.user1.id, is_submitted=True).id
        
        self.add_email_template('reviews-assigned')

    def test_responses_assigned(self):
        self.seed_static_data()

        params = {'event_id' : 1, 'response_ids': [1, 2], 'reviewer_email': 'reviewer@mail.com'}

        response = self.app.post(
            '/api/v1/assignresponsereviewer', 
            headers=self.get_auth_header_for('eventadmin@mail.com'), 
            data=params)

        self.assertEqual(response.status_code, 201)

        response_reviewers = (db.session.query(ResponseReviewer)
                   .join(Response, ResponseReviewer.response_id == Response.id)
                   .filter_by(application_form_id=1).all())

        self.assertEqual(len(response_reviewers), 2)
        
        for rr in response_reviewers:
            self.assertEqual(rr.reviewer_user_id, self.reviewer_user_id)

    def test_response_for_different_event_forbidden(self):
        self.seed_static_data()

        params = {'event_id' : 1, 'response_ids': [1, 2, self.event2_response_id], 'reviewer_email': 'reviewer@mail.com'}

        response = self.app.post(
            '/api/v1/assignresponsereviewer', 
            headers=self.get_auth_header_for('eventadmin@mail.com'), 
            data=params)

        self.assertEqual(response.status_code, 403)

    def test_delete(self):
        """Test that a review assignment can be deleted."""
        self.seed_static_data()

        # Assign a reviewer
        response_id = self.response1.id
        self.add_response_reviewer(response_id, self.reviewer_user_id)

        params = {'event_id' : 1, 'response_id': self.response1.id, 'reviewer_user_id': self.reviewer_user_id}

        response = self.app.delete(
            '/api/v1/assignresponsereviewer', 
            headers=self.get_auth_header_for('eventadmin@mail.com'), 
            data=params)

        self.assertEqual(response.status_code, 200)

        # Check that it was actually deleted
        response_reviewer = db.session.query(ResponseReviewer).filter_by(response_id=response_id, reviewer_user_id=self.reviewer_user_id).first()
        self.assertIsNone(response_reviewer)

    def test_delete_not_allowed_if_completed(self):
        """Test that a review assignment can't be deleted if the review has been completed."""
        self.seed_static_data()

        # Assign a reviewer and create a review resposne
        response_id = self.response1.id
        self.add_response_reviewer(response_id, self.reviewer_user_id)
        self.add_review_response(self.reviewer_user_id, response_id)

        params = {'event_id' : 1, 'response_id': self.response1.id, 'reviewer_user_id': self.reviewer_user_id}

        response = self.app.delete(
            '/api/v1/assignresponsereviewer', 
            headers=self.get_auth_header_for('eventadmin@mail.com'), 
            data=params)

        self.assertEqual(response.status_code, 400)