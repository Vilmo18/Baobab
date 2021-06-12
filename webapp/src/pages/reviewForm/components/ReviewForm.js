import React, { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { isEqual } from 'lodash';
import {
  applicationFormService,
  updateApplicatForm,
  createApplicationForm
} from '../../../services/applicationForm/applicationForm.service';
import { langObject } from '../../../pages/createApplicationForm/components/util';
import { eventService } from '../../../services/events';
import { reviewService } from '../../../services/reviews';
import FormCreator from '../../../components/form/FormCreator';

const ReviewForm = (props) => {
  const { languages } = props;
  const { t } = useTranslation();
  const lang = [...languages];
  const [formDetails, setFormDetails] = useState({});
  const [reviewFormDetails, setReviewFormDetails] = useState({});
  const [isCreateMode, setIsCreateMode] = useState(true);

  const [language, setLanguage] = useState({
    label: lang && lang[0]? lang[0].description : 'English',
    value: lang && lang[0]? lang[0].code : 'en'
  });

  const [dragId, setDragId] = useState();
  const [applyTransition, setApplytransition] = useState(false);
  const [parentDropable, setParentDropable] = useState(true);
  const [homeRedirect, setHomeRedirect] = useState(false);
  const [isInCreateMode, setCreateMode] = useState(true);
  const [initialState, setInitialState] = useState(null);
  const [errorResponse, setErrorResponse] = useState(null);
  const [disableSaveBtn, setDisableSaveBtn] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [leaveStage, setLeaveStage] = useState(false);
  const [showingModal, setShowingModal] = useState(false);
  const [isNewStage, setIsNewStage] = useState(false);

  const [event, setEvent] = useState({
    loading: true,
    event: null,
    error: null,
  });
  console.log('***** ', event);
  const [stage, setStage] = useState({
    loading: true,
    stage: null,
    error: null,
  });
  const [currentStage, setCurrentStage] = useState(0);
  const [appSections, setAppSections] = useState([]);

  const [sections, setSections] = useState([{
    id: `${Math.random()}`,
    name: langObject(lang, t('Untitled Section')),
    description: langObject(lang, ''),
    order: 1,
    questions: [
      {
        id: `${Math.random()}`,
        surrogate_id: 1,
        description: langObject(lang, ''),
        order: 1,
        headline: langObject(lang, ''),
        placeholder: langObject(lang, ''),
        type: null,
        options: langObject(lang, null),
        value: langObject(lang, ''),
        label: langObject(lang, ''),
        required: false,
        validation_regex: langObject(lang, null),
        validation_text: langObject(lang, ''),
        question_id: null,
        weight: 0,
      }
    ]
  }]);
  // const saved = _.isEqual(initialState, sections);
  let maxSurrogateId = 1;
  sections.forEach(s => {
    if (s.backendId > maxSurrogateId) {
      maxSurrogateId = s.backendId;
    }
    s.questions.forEach(q => {
      if (q.backendId > maxSurrogateId) {
        maxSurrogateId = q.backendId
      }
      if (q.surrogate_id > maxSurrogateId) {
        maxSurrogateId = q.surrogate_id
      }
    })
  });
 
  useEffect(() => {
    const eventId = props.event.id;
    reviewService.getReviewStage(eventId)
    .then(res => {
      setStage({
        loading: false,
        stage: res.data,
        error: res.error
      })
    });
    applicationFormService.getDetailsForEvent(eventId)
      .then(res => {
        const formSpec = res.formSpec;
        const sections = formSpec && formSpec.sections;
        if (sections) {
          setAppSections(sections);
          setFormDetails({
            ...formDetails,
            applicationFormId: formSpec.id
          })
        }
    })
  }, []);

  useEffect(() => {
    if (!stage.loading) {
      if(stage.stage) {
        setCurrentStage(stage.stage.current_stage);
      } else {
        setCurrentStage(1);
      }
    }
  }, [stage]);

  useEffect(() => {
    const eventId = props.event.id;
    if (currentStage && !event.loading) {
      reviewService.getReviewFormDetails(eventId, currentStage)
      .then(res => {
        if (res.data) {
          const mapedQuestions = res.data.sections.map(s => {
            const questions = s.questions.map(q => {
              const type = q.type;
              q = {
                ...q,
                id: `${Math.random()}`,
                backendId: q.id,
                required: false,
                type: type === 'long_text' ? 'long-text' : type
              }
              return q
            });
            s = {
              ...s,
              name: s.name ? s.name : s.headline,
              id: `${Math.random()}`,
              backendId: s.id,
              questions: questions
            }
            return s
          })
          setFormDetails({
            isOpen: res.data.is_open,
            eventId: res.data.event_id,
            id: res.data.id,
            applicationFormId: res.data.application_form_id,
            stage: res.data.stage,
            deadline: res.data.deadline,
            active: res.data.active
          })
          setCreateMode(false);
          setInitialState(mapedQuestions);
          setSections(mapedQuestions);
          setLeaveStage(false)
        } else {
          setSections([{
            id: `${Math.random()}`,
            name: langObject(lang, t('Untitled Section')),
            description: langObject(lang, ''),
            order: 1,
            questions: [
              {
                id: `${Math.random()}`,
                surrogate_id: 1,
                description: langObject(lang, ''),
                order: 1,
                headline: langObject(lang, ''),
                placeholder: langObject(lang, ''),
                type: null,
                options: langObject(lang, null),
                value: langObject(lang, ''),
                label: langObject(lang, ''),
                required: false,
                validation_regex: langObject(lang, null),
                question_id: null,
                validation_text: langObject(lang, ''),
                weight: 0,
              }
            ]
          }])
          setFormDetails({
            ...formDetails,
            isOpen: props.event.is_review_open,
            eventId: event.event.id,
            stage: currentStage,
            deadline: event.event.review_close,
            active: currentStage !== 1 ? true : false
          })
          setCreateMode(true);
        }
      })
    }
  }, [currentStage])

  const addSection = () => {
    setTimeout(() => setSections([...sections, {
      id: `${Math.random()}`,
      name: langObject(lang, t('Untitled Section')),
      description: langObject(lang, ''),
      order: sections.length + 1,
      questions: [
        {
          id: `${Math.random()}`,
          surrogate_id: maxSurrogateId + 1,
          description: langObject(lang, ''),
          order: 1,
          headline: langObject(lang, ''),
          placeholder: langObject(lang, ''),
          type: null,
          options: langObject(lang, null),
          value: langObject(lang, ''),
          label: langObject(lang, ''),
          required: false,
          validation_regex: langObject(lang, null),
          validation_text: langObject(lang, ''),
          question_id: null,
          weight: 0,
        }
      ]
    }]), 1);
  }

  const addQuestion = (sectionId) => {
    const surrogateId = maxSurrogateId + 1
    const sction = sections.find(s => s.id === sectionId);
    const qsts = sction.questions;
    const qst = {
      id: `${Math.random()}`,
      surrogate_id: surrogateId,
      description: langObject(lang, ''),
      order: qsts.length + 1,
      headline: langObject(lang, ''),
      placeholder: langObject(lang, ''),
      type: null,
      options: langObject(lang, null),
      value: langObject(lang, ''),
      label: langObject(lang, ''),
      required: false,
      validation_regex: langObject(lang, null),
      validation_text: langObject(lang, ''),
      question_id: null,
      weight: 0,
    }
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...s, questions: [...qsts, qst]};
      }
      return s;
    });
    setSections(updatedSections);
    setApplytransition(false);
    // setQuestionAnimation(false);
  }

  const addAnswerFromAppForm = (sectionId) => {
    const surrogateId = maxSurrogateId + 1;
    const sction = sections.find(s => s.id === sectionId);
    const qsts = sction.questions;
    const qst = {
      id: `${Math.random()}`,
      surrogate_id: surrogateId,
      description: langObject(lang, ''),
      order: qsts.length + 1,
      headline: langObject(lang, ''),
      type: 'information',
      required: false,
      question_id: null,
      placeholder: langObject(lang, null),
      options: langObject(lang, null),
      validation_regex: langObject(lang, null),
      validation_text: langObject(lang, null),
    }
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...s, questions: [...qsts, qst]};
      }
      return s;
    });
    setSections(updatedSections);
    setApplytransition(false);
  }

  const handleSave = async () => {
    const sectionsToSave = sections.map(s => {
      const questions = s.questions.map(q => {
        if (q.backendId) {
          if (q.type === 'information') {
            q = {
              id: q.backendId,
              description: q.description,
              order: q.order,
              headline: q.headline,
              type: q.type,
              is_required: q.required,
              question_id: q.question_id,
              weight: q.weight,
              options: langObject(lang, null),
              placeholder: langObject(lang, null),
              validation_regex: langObject(lang, null),
              validation_text: langObject(lang, null),
            }
          } else {
            q = {
              id: q.backendId,
              depends_on_question_id: q.depends_on_question_id,
              headline: q.headline,
              description: q.description,
              is_required: q.required,
              options: q.options,
              order: q.order,
              placeholder: q.placeholder,
              type: q.type,
              validation_regex: q.validation_regex,
              validation_text: q.validation_text,
              question_id: q.question_id,
              weight: q.weight,
            }
          }
        } else {
          if (q.type === 'information') {
            q = {
              surrogate_id: q.surrogate_id,
              description: q.description,
              order: q.order,
              headline: q.headline,
              type: q.type,
              is_required: q.required,
              question_id: q.question_id,
              weight: q.weight,
              options: langObject(lang, null),
              placeholder: langObject(lang, null),
              validation_regex: langObject(lang, null),
              validation_text: langObject(lang, null),
            }
          } else {
            q = {
              surrogate_id: q.surrogate_id,
              depends_on_question_id: q.depends_on_question_id,
              headline: q.headline,
              description: q.description,
              is_required: q.required,
              options: q.options,
              order: q.order,
              placeholder: q.placeholder,
              type: q.type,
              validation_regex: q.validation_regex,
              validation_text: q.validation_text,
              question_id: q.question_id,
              weight: q.weight
            }
          }
        }
        return q
      });
      if (s.backendId) {
        s = {
          id: s.backendId,
          depends_on_question_id: s.depends_on_question_id,
          description: s.description,
          headline: s.name,
          order: s.order,
          questions: questions
        }
      } else {
        s = {
          description: s.description,
          headline: s.name,
          order: s.order,
          questions: questions
        }
      }
      return s
    });
    const {
      id, eventId, isOpen, applicationFormId,
      stage, deadline, active
    } = formDetails;
    if (!isInCreateMode) {
      if (!isSaved) {
        const res = await reviewService.updateReviewForm({
          id, eventId, isOpen, applicationFormId,
          stage, deadline, active, sectionsToSave
        });
        if(!res.error) {
          setIsSaved(true);
          setHomeRedirect(true);
        } else {
          if (res.data && res.data.message) {
            setErrorResponse(res.data.message.event_id);
          } else {
            setErrorResponse(res.error);
          }
        }
      }
    } else {
        const res = await reviewService.createReviewForm({
          eventId, isOpen, applicationFormId,
          stage, deadline, active, sectionsToSave
        });
        if (res.status === 201) {
          setIsSaved(true);
          setHomeRedirect(true);
        } else {
          if (res.data && res.data.message) {
            setErrorResponse(res.data.message.event_id);
          } else {
            setErrorResponse(res.error);
          }
        }
    }
  }

  return (
    <FormCreator
      languages={lang}
      event={props.event}
      t={t}
      sections={sections}
      setSections={setSections}
      language={language}
      setLanguage={setLanguage}
      dragId={dragId}
      setDragId={setDragId}
      applyTransition={applyTransition}
      setApplytransition={setApplytransition}
      parentDropable={parentDropable}
      setParentDropable={setParentDropable}
      homeRedirect={homeRedirect}
      initialState={initialState}
      errorResponse={errorResponse}
      disableSaveBtn={disableSaveBtn}
      setDisableSaveBtn={setDisableSaveBtn}
      events={event}
      setEvent={setEvent}
      eventService={eventService}
      addSection={addSection}
      handleSave={handleSave}
      isSaved={isSaved}
      isReview={true}
      addQuestion={addQuestion}
      addAnswerFromAppForm={addAnswerFromAppForm}
      appSections={appSections}
      stage={stage}
      currentStage={currentStage}
      setCurrentStage={setCurrentStage}
      leaveStage={leaveStage}
      setLeaveStage={setLeaveStage}
      showingModal={showingModal}
      setShowingModal={setShowingModal}
      isNewStage={isNewStage}
      setIsNewStage={setIsNewStage}
     />
  )
}

export default ReviewForm;