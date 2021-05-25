import React, { useState, useEffect, createRef } from 'react';
import { Redirect, Prompt } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Trans } from 'react-i18next';
import { default as ReactSelect } from "react-select";
import _ from 'lodash';
import {
  applicationFormService,
  updateApplicationForm,
  createApplicationForm
} from '../../../services/applicationForm/applicationForm.service';
import { eventService } from '../../../services/events';
import Section from './Section';
import Loading from '../../../components/Loading';
import {
  option, langObject, AnimateSections,
  drop, drag
 } from './util';
 import { dateFormat, TopBar } from '../../../utils/forms';
 import FormCreator from '../../../components/form/FormCreator';


const ApplicationForm = (props) => {
  const { languages } = props;
  const { t } = useTranslation();
  const lang = languages;
  const [nominate, setNominate] = useState(false);
  const [formDetails, setFormDetails] = useState({});

  const [language, setLanguage] = useState({
    label: lang && lang[0]? lang[0].description : 'English',
    value: lang && lang[0]? lang[0].code : 'en'
  });

  const [dragId, setDragId] = useState();
  const [applyTransition, setApplytransition] = useState(false);
  const [parentDropable, setParentDropable] = useState(true);
  const [homeRedirect, setHomeRedirect] = useState(false);
  const [isInCreateMode, setCreateMode] = useState(false);
  const [initialState, setInitialState] = useState(null);
  const [errorResponse, setErrorResponse] = useState(null);
  const [disableSaveBtn, setDisableSaveBtn] = useState(false)

  const [event, setEvent] = useState({
    loading: true,
    event: null,
    error: null,
  });


  const [sections, setSections] = useState([{
    id: `${Math.random()}`,
    name: langObject(lang, t('Untitled Section')),
    description: langObject(lang, ''),
    order: 1,
    depends_on_question_id: 0,
    show_for_values: langObject(lang, null),
    key: null,
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
        key: null,
        depends_on_question_id: 0,
        show_for_values: langObject(lang, null),
        validation_regex: langObject(lang, null),
        validation_text: langObject(lang, ''),
      }
    ]
  }]);
  const [isSaved, setIsSaved] = useState(false);
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
  })

  useEffect(() => {
    const eventId = props.event.id;
    applicationFormService.getDetailsForEvent(eventId)
      .then(res => {
        if (res) {
          const formSpec = res.formSpec;
          if (formSpec.sections) {
            const mapedQuestions = formSpec.sections.map(s => {
              const questions = s.questions.map(q => {
                const type = q.type;
                q = {
                  ...q,
                  id: `${Math.random()}`,
                  backendId: q.id,
                  required: q.is_required,
                  type: type === 'long_text' ? 'long-text' : type
                }
                return q
              });
              s = {
                ...s,
                id: `${Math.random()}`,
                backendId: s.id,
                questions: questions
              }
              return s
            })
  
            setNominate(formSpec.nominations);
            setFormDetails({
              isOpen: props.event.is_application_open,
              id: formSpec.id,
              eventId: eventId
            })
            setInitialState(mapedQuestions);
            setSections(mapedQuestions);
          } else {
            setFormDetails({
              isOpen: props.event.is_application_open,
              eventId: eventId
            })
            setCreateMode(true);
          }
        } else {
          setFormDetails({
            isOpen: props.event.is_application_open,
            eventId: eventId
          })
          setCreateMode(true);
        }
      }).catch(err => {
        setErrorResponse('Error occured ' + err)
    })
  }, []);

  const addSection = () => {
    setTimeout(() => setSections([...sections, {
      id: `${Math.random()}`,
      name: langObject(lang, t('Untitled Section')),
      description: langObject(lang, ''),
      order: sections.length + 1,
      key: null,
      depends_on_question_id: 0,
      show_for_values: langObject(lang, null),
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
          key: null,
          depends_on_question_id: 0,
          show_for_values: langObject(lang, null),
          validation_regex: langObject(lang, null),
          validation_text: langObject(lang, ''),
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
      key: null,
      depends_on_question_id: 0,
      show_for_values: langObject(lang, null),
      validation_regex: langObject(lang, null),
      validation_text: langObject(lang, ''),
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

  const handleSave = async () => {
    const sectionsToSave = sections.map(s => {
      const questions = s.questions.map(q => {
        if (q.backendId) {
          q = {
            id: q.backendId,
            depends_on_question_id: q.depends_on_question_id,
            headline: q.headline,
            description: q.description,
            is_required: q.required,
            key: q.key,
            options: q.options,
            order: q.order,
            placeholder: q.placeholder,
            show_for_values: q.show_for_values,
            type: q.type,
            validation_regex: q.validation_regex,
            validation_text: q.validation_text
          }
        } else {
          q = {
            surrogate_id: q.surrogate_id,
            depends_on_question_id: q.depends_on_question_id,
            headline: q.headline,
            description: q.description,
            is_required: q.required,
            key: q.key,
            options: q.options,
            order: q.order,
            placeholder: q.placeholder,
            show_for_values: q.show_for_values,
            type: q.type,
            validation_regex: q.validation_regex,
            validation_text: q.validation_text
          }
        }
        return q
      });
      if (s.backendId) {
        s = {
          id: s.backendId,
          depends_on_question_id: s.depends_on_question_id,
          description: s.description,
          key: s.key,
          name: s.name,
          order: s.order,
          show_for_values: s.show_for_values,
          questions: questions
        }
      } else {
        s = {
          depends_on_question_id: s.depends_on_question_id,
          description: s.description,
          key: s.key,
          name: s.name,
          order: s.order,
          show_for_values: s.show_for_values,
          questions: questions
        }
      }
      return s
    });
    const { id, eventId, isOpen } = formDetails;
    if (!isInCreateMode) {
      if (!isSaved) {
        const res = await updateApplicationForm(id, eventId, isOpen, nominate, sectionsToSave);
        if(res.status === 200) {
          setIsSaved(true);
          setHomeRedirect(true);
        } else {
          if (res.data && res.data.message) {
            setErrorResponse(res.data.message.event_id);
          } else {
            setErrorResponse(res);
          }
        }
      }
    } else {
        const res = await createApplicationForm(eventId, isOpen, nominate, sectionsToSave);
        console.log(res);
        if (res.status === 201) {
          setIsSaved(true);
          setHomeRedirect(true);
        } else {
          if (res.data && res.data.message) {
            setErrorResponse(res.data.message.event_id);
          } else {
            setErrorResponse(res);
          }
        }
    }
  }

  return (
    <FormCreator
      languages={languages}
      event={props.event}
      t={t}
      sections={sections}
      setSections={setSections}
      nominate={nominate}
      setNominate={setNominate}
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
      addQuestion={addQuestion}
     />
  )
}

export default ApplicationForm;