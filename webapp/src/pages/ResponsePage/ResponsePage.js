
import React, { Component } from 'react'
import "react-table/react-table.css";
import { withTranslation } from 'react-i18next';
import './ResponsePage.css'
import { applicationFormService } from '../../services/applicationForm/applicationForm.service'
import { fetchResponse } from '../../services/responsePage/responsePage.service'
import { tagList } from '../../services/taglist/TagList.service'
import { eventService } from '../../services/events/events.service'

class ResponsePage extends Component {
    constructor(props) {
        super(props);
        this.state = {
            tagMenu: false
        }
    };

    componentDidMount() {
        this.fetchForm()
        this.fetchData()
        this.fetchTags()
       // this.fetchEvent()
    }


      // Fetch Tags
    fetchTags() {
        tagList().then(response => {
            this.setState({
                tagList: response
            })
        })
    }
  

        // Fetch Event Details
        fetchEvent() {
            eventService.getEvent().then(response => {
                this.setState({
                    eventDetails: response
                })
            })
        }


    // Fetch Form
    fetchForm() {
        applicationFormService.getForEvent(this.props.event.id).then(response => {
            this.setState({
                applicationForm: response.formSpec
            })
        })

    }


    // Fetch Data
    fetchData() {
        let params = {
            id: this.props.match.params.id
        }
        fetchResponse(params).then(response => {
            this.setState({
                applicationData: response
            })
        })
    }


    // Go Back
    goBack() {
        this.props.history.goBack();
    }


    // Generate Applciation Status
    applicationStatus() {
        const data = this.state.applicationData;

        if (data) {
            let unsubmitted = !data.is_submitted && !data.is_withdrawn;
            let submitted = data.is_submitted;
            let withdrawn = data.is_withdrawn;

            if (unsubmitted) {
                return ["unsubmitted" + " " + data.started_timestamp]
            }
            if (submitted) {
                return ["submitted" + " " + data.submitted_timestamp]
            }
            if (withdrawn) {
                return ["withdrawn" + " " + data.withdrawn_timestamp]
            }
        }
    }


    renderTags() {
        const data = this.state.applicationData;
        if (data) {
            let tags = data.tags.map(tag => {
                return <span class="badge badge-info dark">{tag.headline}</span>
            })
            return tags
        }

    }



    // Render Sections
    renderSections() {
        const applicationForm = this.state.applicationForm;
        const applicationData = this.state.applicationData;
        let html = [];
        // Translation
        const t = this.props.t;

        // main function
        if (applicationForm && applicationData) {
            applicationForm.sections.forEach(section => {
                html.push(<div key={section.name} className="section">
                    { /*Heading*/}
                    <div className="flex baseline"><h3>{section.name}</h3></div>
                    { /*Q & A*/}
                    <div className="Q-A">
                        {this.renderQuestions(section)}
                    </div>
                </div>)
            })
        }

        return html
    }



    // Render Questions 
    renderQuestions(section) {
        let questions = section.questions.map(q => {
            return <div key={q.id} className="question-answer-block">
                <p>{q.headline}</p>
                <h6>{this.renderAnswer(q.id, q.type)}</h6>
            </div>
        })
        return questions
    }


    // Render Answers 
    renderAnswer(id, type) {
        const applicationData = this.state.applicationData;
        const baseUrl = process.env.REACT_APP_API_URL;
        let answers;

        applicationData.answers.forEach(a => {
            if (a.question_id == id) {
                formatAnswer(a, type)
            }
        })

        // format aswerers 
        function formatAnswer(a, type) {
            // file
            if (type == "file") {
                answers = <a className="answer file" key={a.value} target="_blank" href={baseUrl + "/api/v1/file?filename=" + a.value}>{a.value}</a>
            }
            // multi-file
            if (type == "multi-file") {
                let files = [];
                a.value.forEach((file => {
                    if (file) {
                        files.push(
                            <div key={a.headline}><a key={a.headline} target="_blank" href={baseUrl + "/api/v1/file?filename=" + file} className="answer">{a.value}</a></div>
                        )
                    }
                }))
                answers = <div key={a.headline}>{files}</div>
            }
            // choice
            if (type.includes("choice")) {
                let choices = [];
                a.options.forEach(opt => {
                    if (a.value == opt.valuel) {
                        choices.push(<div key={opt.label}><label className="answer">{opt.label}</label></div>)
                    }
                })
                answers = <div key={choices}>{choices}</div>
            }
            // text
            if (type.includes("text")) {
                answers = <div key={a.headline}><p className="answer">{a.value}</p></div>
            }
        }

        return answers
    }


    toggleTags(list) {
        this.setState({
            tagMenu: list ? false : true
        })
    }


    render() {
        const { applicationForm, applicationData, tagList, tagMenu } = this.state
        const applicationStatus = this.applicationStatus();
        const renderSections = this.renderSections();
        const tags = this.renderTags()

        // Translation
        const t = this.props.t;

        return (
            <div className="table-wrapper">

                {/*Add Tags Modal */}
                <div class="modal fade" id="exampleModal" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
                    <div class="modal-dialog" role="document">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="exampleModalLabel">Add Tags</h5>
                                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            </div>
                            <div class="modal-body">
                                <form>
                                    <div>
                                        <label>English</label>
                                        <input placeHolder="enter tag name"></input>
                                    </div>
                                    
                                </form>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                                <button type="button" class="btn btn-primary">Save</button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Headings */}
                {applicationData &&
                    <div className="headings-lower">
                        <div className="user-details">
                            <h2>{applicationData.user_title} {applicationData.firstname} {applicationData.lastname}</h2>
                            <div className="tags">{tags}  <span onClick={(e) => this.toggleTags(tagMenu)} className="badge add-tags">Add tag</span></div>

                            {/*Tag List*/}
                            <div className={tagMenu ? "tag-response show" : "tag-response"}>
                                {tagList &&
                                    tagList.map(val => {
                                        return <div className="tag-item" key={val.id} >
                                            <button class="btn tag">{val.name}</button>
                                        </div>
                                    })}
                                <button data-toggle="modal" data-target="#exampleModal" type="button" className="btn btn-primary" data-toggle="modal" data-target="#exampleModal">
                                    Launch demo modal
                            </button>
                            </div>

                        </div>

                        {/* User details Right Tab */}
                        <div>
                            <div className="user-details right"><label>{t('Application Status')}</label> <p>{applicationStatus}</p>
                                <button className="btn btn-primary" onClick={((e) => this.goBack(e))}>Back</button>
                            </div>

                        </div>
                    </div>
                }

                {/*Response Data*/}
                {applicationData &&
                    <div className="response-details">
                        {renderSections}
                    </div>
                }

            </div>

        )
    }
}

export default withTranslation()(ResponsePage);


