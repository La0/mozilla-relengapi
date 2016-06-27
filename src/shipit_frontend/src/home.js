import React from 'react';
import {Link} from 'react-router';
import {routes} from './layout';

const services = routes.keySeq()
  .filter(x => x !== "home")
  .reduce((result, x) => {
      if (result[result.length-1].length === 3) result.push([]);
      result[result.length -1].push(routes.get(x).toJS());
      return result;
    }, [[]]);

export const Home = () => (
  <div>
    <div className="container">
      This is the home page.
      <br />
      <Link to="/dashboard" className="btn btn-primary">
        Go to dashboard
      </Link>
    </div>
  </div>
)
Home.__name__ = 'Home'
export default Home;
