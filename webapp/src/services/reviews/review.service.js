import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const reviewService = {
  getReviewForm,
  submit,
  getReviewAssignments,
  assignReviews,
  getReviewSummary,
  getReviewHistory
};

function getReviewForm(eventId, skip) {
  return axios
    .get(baseUrl + "/api/v1/review?event_id=" + eventId + "&skip=" + skip, {
      headers: authHeader()
    })
    .then(function(response) {
      return {
        form: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        form: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function submit(responseId, reviewFormId, scores) {
  let review = {
    response_id: responseId,
    review_form_id: reviewFormId,
    scores: scores
  };

  return axios
    .post(baseUrl + "/api/v1/reviewresponse", review, { headers: authHeader() })
    .then(function(response) {
      return {
        error: ""
      };
    })
    .catch(function(error) {
      return {
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function getReviewAssignments(eventId) {
  return axios
    .get(baseUrl + "/api/v1/reviewassignment?event_id=" + eventId, {
      headers: authHeader()
    })
    .then(function(response) {
      return {
        reviewers: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        reviewers: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function assignReviews(eventId, reviewers) {
  return axios
    .all(
      reviewers.map(review =>
        assignReview(eventId, review.email, review.reviews_to_assign)
      )
    )
    .then(function(response) {
      return {
        error: ""
      };
    })
    .catch(function(error) {
      //TODO: This probably won't work as expected with
      return {
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function assignReview(eventId, reviewerUserEmail, numReviews) {
  let assignment = {
    event_id: eventId,
    reviewer_user_email: reviewerUserEmail,
    num_reviews: numReviews
  };

  return axios
    .post(baseUrl + "/api/v1/reviewassignment", assignment, {
      headers: authHeader()
    })
    .then(function(response) {
      return {
        error: ""
      };
    })
    .catch(function(error) {
      return {
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function getReviewSummary(eventId) {
  return axios
    .get(baseUrl + "/api/v1/reviewassignment/summary?event_id=" + eventId, {
      headers: authHeader()
    })
    .then(function(response) {
      return {
        reviewSummary: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        reviewSummary: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function getReviewHistory(eventId) {
  return axios
    .get(baseUrl + "/api/v1/reviewhistory?event_id=" + eventId, {
      headers: authHeader()
    })
    .then(function(response) {
      return {
        reviewHistory: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        reviewHistory: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}
