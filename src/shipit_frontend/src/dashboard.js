import React from 'react';
import { Link } from 'react-router';
import { connect } from 'react-redux';
import { Map } from 'immutable';
import { combineReducers } from 'redux'
import {routes} from './layout';
import { race, call, fork, put } from 'redux-saga/effects'
import { takeLatest, delay } from 'redux-saga';
import { fetchJSON } from './common';

// Recent bugs assigned to sylvestre
const BUGZILLA_URL = 'https://bugzilla.mozilla.org/rest/bug?assigned_to=sledru@mozilla.com&limit=10&last_change_time=2016-06-01'
const TIMEOUT = 30;

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
const bugsReducer = (state = Map(), action) => {
  switch(action.type) {
    case 'DASHBOARD.BUGS.FETCH':
      // Initial state
      return state.set('loading', true);

    case 'DASHBOARD.BUGS.FETCH_SUCCESS':
      // Load bugs from payload
      return state.merge({
        'error' : false,
        'loading' : false,
        'items' : action.payload.bugs,
      });

    case 'DASHBOARD.BUGS.FETCH_FAILED':
      // Handle error
      return state.merge({
        'error' : true,
        'loading' : false,
        'items' : [],
      });

    default:
      return state;
  }
}

export const reducers = combineReducers({
  'bugs' : bugsReducer,
})

/* Sagas */

const fetchBugsSaga = () => {
  return function*(){

    // Fetch data with a timeout limit
    const { response, timeout } = yield race({
        response: call(fetchJSON, BUGZILLA_URL),
        timeout: call(delay, TIMEOUT * 1000)
    });

    if (response) {
      if (response instanceof Error) {
        yield put({
          type: 'DASHBOARD.BUGS.FETCH_FAILED',
          payload: response
        });
      } else {
        yield put({
          type: 'DASHBOARD.BUGS.FETCH_SUCCESS',
          payload: response
        });
      }
    } else {
      yield put({
        type: 'DASHBOARD.BUGS.FETCH_FAILED',
        payload: 'Timeout (' + TIMEOUT + ') reached!'
      });
    }
  }
}

const watchFetchBugs = () => {
  return function* () {
    // On a bugs fetch signal, actually fetch !
    yield takeLatest('DASHBOARD.BUGS.FETCH', fetchBugsSaga());
  };
};


const initialFetch = () => {
  return function*(){
    yield put(fetchBugs());
  }
}

export const sagas = [

  // Fetch bugs when needed
  fork(watchFetchBugs()),

  // Send signal to start fetching
  // Must be after watcher
  fork(initialFetch()),
]

/* Mappings */
const mapStateToProps = state => {
  let input = state.toObject()
  if(!input.dashboard)
    return {}
  return {
    'bugs' : input.dashboard.bugs.toJS()
  }
}

const mapDispatchToProps = dispatch => {

  return {};
}


/* Components */
const Bug = ({id, product, summary}) => (
  <div className="row">
    <div className="col-xs-12">
      <h5>{summary}</h5>
      BUG #{id} on {product}
      <hr />
    </div>
  </div>
)
Bug.__name__ = 'Bug'

export const Dashboard = props => {
  let {
    bugs = {},
  } = props;
  return (
    <div className="container-fluid">
      {(!bugs || bugs.loading == true) ?
      <p className="alert alert-info">Loading...</p>
      :
      <div>
        {bugs.items && bugs.items.map(bug => <Bug key={bug.id} {...bug} />)}
      </div>}
    </div>
  )
}
Dashboard.__name__ = 'Dashboard'

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Dashboard);
