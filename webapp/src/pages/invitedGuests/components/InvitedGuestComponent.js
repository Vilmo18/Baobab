import React, { Component } from "react";
import { withRouter } from "react-router";
import { invitedGuestServices } from "../../../services/invitedGuests/invitedGuests.service";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import { createColClassName } from "../../../utils/styling/styling";
import "react-table/react-table.css";
import validationFields from "../../../utils/validation/validationFields";
import { run, ruleRunner } from "../../../utils/validation/ruleRunner";

import {
  requiredText,
  requiredDropdown,
  validEmail
} from "../../../utils/validation/rules.js";
import {
  getTitleOptions,
  getGenderOptions,
} from "../../../utils/validation/contentHelpers";

const fieldValidations = [
  ruleRunner(validationFields.email, validEmail),
  ruleRunner(validationFields.role, requiredDropdown)
];

const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;

class InvitedGuests extends Component {
  constructor(props) {
    super(props);
    this.state = {
      isLoading: true,
      isError: false,
      guestList: [],
      user: {},
      addedSucess: false,
      notFound: false,
      buttonClicked: false,
      conflict: false,
      error: "",
      errors: null
    };
  } 
  getGuestList() {
    this.setState({ loading: true });
    invitedGuestServices.getInvitedGuestList(DEFAULT_EVENT_ID).then(result => {
      this.setState({
        loading: false,
        guestList: result.form,
        error: result.error
      });
    });
  }

  checkOptionsList(optionsList) {
    if (Array.isArray(optionsList)) {
      return optionsList;
    } else return [];
  }

  componentDidMount() {
    this.getGuestList();
    Promise.all([
      getTitleOptions,
      getGenderOptions,
    ]).then(result => {
      this.setState({
        titleOptions: this.checkOptionsList(result[0]),
        genderOptions: this.checkOptionsList(result[1]),
      });
    });
  }

  handleChangeDropdown = (name, dropdown) => {
    this.setState(
      {
        user: {
          ...this.state.user,
          [name]: dropdown.value
        }
      },
      function() {
        let errorsForm = run(this.state.user, fieldValidations);
        this.setState({ errors: { $set: errorsForm } });
      }
    );
  };

  handleChange = field => {
    return event => {
      this.setState(
        {
          user: {
            ...this.state.user,
            [field.name]: event.target.value
          }
        },
        function() {
          let errorsForm = run(this.state.user, fieldValidations);
          this.setState({ errors: { $set: errorsForm } });
        }
      );
    };
  };


  buttonSubmit() {
    invitedGuestServices
      .addInvitedGuest(this.state.user.email, DEFAULT_EVENT_ID, this.state.user.role)
      .then(response => {
        if (response.msg === "succeeded") {
          this.getGuestList();
          this.setState({
            addedSucess: true,
            conflict: false,
            notFound: false
          });
        } else if (response.msg === "404") {
          this.setState({
            addedSucess: false,
            notFound: true,
            conflict: false
          });
        } else if (response.msg === "409") {
          this.setState({
            notFound: false,
            addedSucess: false,
            conflict: true
          });
        } else {
          this.setState({
            error: response.error
          });
        }
      });
  }

  submitCreate = () => {

  }

  render() {
    const threeColClassName = createColClassName(12, 4, 4, 4);  //xs, sm, md, lg

    const { loading, error } = this.state;
    const roleOptions = invitedGuestServices.getRoles();
    let lastGuest;
    if (this.state.guestList !== null) {
      lastGuest = this.state.guestList[this.state.guestList.length - 1];
    }

    if (loading) {
      return (
        <div class="d-flex justify-content-center">
          <div class="spinner-border" role="status">
            <span class="sr-only">Loading...</span>
          </div>
        </div>
      );
    }

    return (
      <div className="InvitedGuests container-fluid pad-top-30-md">
        {error && <div className={"alert alert-danger"}>{JSON.stringify(error)}</div>}

        <div class="card no-padding-h">
          <p className="h5 text-center mb-1 ">Invited Guests</p>

          <div class="responsive-table">
            {this.state.guestList !== null &&
            this.state.guestList.length > 0 ? (
              <table cellPadding={5} className="stretched round-table">
                <thead>
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Lastname</th>
                    <th scope="col">Email</th>
                    <th scope="col">Role</th>
                    <th scope="col">Affiliation</th>
                  </tr>
                </thead>
                {this.state.guestList.map(user => (
                  <tbody className="white-background" key={user.email}>
                    <tr className="font-size-12">
                      <td>{user.user.firstname}</td>
                      <td>{user.user.lastname}</td>
                      <td>{user.user.email}</td>
                      <td>{user.role}</td>
                      <td>{user.user.affiliation}</td>
                    </tr>
                  </tbody>
                ))}
              </table>
            ) : (
              <div class="alert alert-danger">No invited guests</div>
            )}
          </div>
        </div>

        {this.state.addedSucess && (
          <div class="card flat-card success">
            {" "}
            Successfully added {lastGuest.user.firstname}{" "}
            {lastGuest.user.lastname}
          </div>
        )}
        
        {this.state.addedSucess === false && this.state.conflict && (
          <div class="card flat-card conflict">
            Invited guest with this email already exists.
          </div>
        )}

        <form>
          <div class="card">
            <p className="h5 text-center mb-4">Add Guest</p>
            <div class="row">
              <div class={threeColClassName}>
                <FormTextBox
                  id={validationFields.email.name}
                  type="email"
                  placeholder={validationFields.email.display}
                  onChange={this.handleChange(validationFields.email)}
                  label={validationFields.email.display}
                />
              </div>

              <div class={threeColClassName}>
                <FormSelect
                  options={roleOptions}
                  id={validationFields.role.name}
                  placeholder={validationFields.role.display}
                  onChange={this.handleChangeDropdown}
                  label={validationFields.role.display}
                />
              </div>
              <div class={threeColClassName}>
                {!this.state.notFound &&
                  <button
                    type="button"
                    class="btn btn-primary stretched margin-top-32"
                    onClick={() => this.buttonSubmit()}
                  >
                    Add
                  </button>
                }
                {!this.state.addedSucess && this.state.notFound && 
                  <span className="text-warning not-found">
                    User does not exist in Baobab, please add these details:
                  </span>
                }
              </div>
            </div>
            
            {!this.state.addedSucess && this.state.notFound && 
              <div>
                <div class="row">
                  <div className={threeColClassName}>
                    <FormSelect
                      options={this.state.titleOptions}
                      id={validationFields.title.name}
                      placeholder={validationFields.title.display}
                      onChange={this.handleChangeDropdown}
                      label={validationFields.title.display}
                    />
                  </div>
                  <div className={threeColClassName}>
                    <FormTextBox
                      id={validationFields.firstName.name}
                      type="text"
                      placeholder={validationFields.firstName.display}
                      onChange={this.handleChange(validationFields.firstName)}
                      label={validationFields.firstName.display}
                    />
                  </div>
                  <div className={threeColClassName}>
                    <FormTextBox
                      id={validationFields.lastName.name}
                      type="text"
                      placeholder={validationFields.lastName.display}
                      onChange={this.handleChange(validationFields.lastName)}
                      label={validationFields.lastName.display}
                    />
                  </div>
                </div>
                <div class="row">
                  <div className={threeColClassName}>
                    <FormSelect
                      options={this.state.genderOptions}
                      id={validationFields.gender.name}
                      placeholder={validationFields.gender.display}
                      onChange={this.handleChangeDropdown}
                      label={validationFields.gender.display}
                    />
                  </div>
                  <div className={threeColClassName}>
                    <FormTextBox
                      id={validationFields.affiliation.name}
                      type="text"
                      placeholder={validationFields.affiliation.display}
                      onChange={this.handleChange(validationFields.affiliation)}
                      label={validationFields.affiliation.display}
                    />
                  </div>
                  <div className={threeColClassName}>
                    <button
                      type="button"
                      class="btn btn-primary stretched margin-top-32"
                      onClick={() => this.submitCreate()}
                    >
                      Create Invited Guest
                    </button>
                  </div>
                </div>
              </div>
            }

          </div>
        </form>
      </div>
    );
  }
}

export default withRouter(InvitedGuests);
