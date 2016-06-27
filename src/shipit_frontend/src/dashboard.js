import React from 'react';
import { Link } from 'react-router';
import { connect } from 'react-redux';
import { Map, List } from 'immutable';
import { combineReducers } from 'redux'
import {routes} from './layout';
import { fork, put } from 'redux-saga/effects'

const services = routes.keySeq()
  .filter(x => x !== "dashboard")
  .reduce((result, x) => {
      if (result[result.length-1].length === 3) result.push([]);
      result[result.length -1].push(routes.get(x).toJS());
      return result;
    }, [[]]);

/* Actions */
const fetchBugs = () => {
  return {
    type : 'DASHBOARD.BUGS.FETCH',
  }
}

/* Reducers */
const fakeBugsReducer = (state = List(), action) => {
  switch(action.type) {
    case 'DASHBOARD.BUGS.FETCH':
      // Add dummy bugs in state
      return state.push({
        id: 12345,
        title : 'dummy bug #1',
      }).push({
        id: 67890,
        title : 'dummy bug #2',
      });

    default:
      return state;
  }
}

export const reducers = combineReducers({
  bugs: fakeBugsReducer, // TODO Use real bugs provider
})

/* Sagas */

const initialFetch = () => {
  return function*(){
    console.info('Initial fake bugs loading...');
    yield put(fetchBugs());
  };
}

export const sagas = [
  fork(initialFetch())
]

/* Mappings */
const mapStateToProps = state => {
  // Simply give full state for demo
  return state.toJS();
}

const mapDispatchToProps = dispatch => {

  return {};
}


/* Components */
const Bug = ({id, title}) => (
  <div className="row">
    <div className="col-xs-6">
      BUG #{id} : {title}
    </div>
  </div>
)
Bug.__name__ = 'Bug'

export const Dashboard = ({dashboard}) => (
  <div>
    <div className="container-fluid">
      {dashboard.bugs.map(bug =>
        <Bug key={bug.id} {...bug} />
      )}
    </div>
  </div>
)
Dashboard.__name__ = 'Dashboard'

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Dashboard);
