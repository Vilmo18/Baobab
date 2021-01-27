import React from "react";
import { withTranslation } from 'react-i18next';

import MultiFileValue from './MultiFileValue'

const baseUrl = process.env.REACT_APP_API_URL;
const FILE = "file";
const INFORMATION = 'information'
const MULTI_CHOICE = "multi-choice";
const MULTI_FILE = 'multi-file';

function AnswerValue({answer, question, t}) {
  if (answer && answer.question_type) {
    if (answer.question_type === INFORMATION) {
      return "";
    }
  } else {
    if (question && question.type === INFORMATION) {
      return "";
    }
  }

  if (answer && answer.value) {
    if (typeof answer.value === "string") {
      answer.value.trim()
    }
    switch (question.type) {
      case MULTI_CHOICE:
        const opts = question.options || answer.options
        const options = opts.filter(o => o.value === answer.value);
        if (options && options.length > 0) {
          return options[0].label;
        }
        else {
          return answer.value;
        }
      case FILE:
        return <div>
          <a target="_blank" href={baseUrl + "/api/v1/file?filename=" + answer.value}>{t("Uploaded File")}</a>
          <br/>
          <span className="small-text">
            *{t("Note: You may need to change the file name to open the file on certain operating systems")}
          </span>
        </div>
      case MULTI_FILE:
        return <div>
          <MultiFileValue value={answer.value}/>
          <br/>
          <span className="small-text">
            *{t("Note: You may need to change the file name to open the file on certain operating systems")}
          </span>
        </div>
      default:
        return answer.value;
    }
  }
  return t("No answer provided.");
}

export default withTranslation()(AnswerValue);
