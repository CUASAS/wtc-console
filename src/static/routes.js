import React from 'react';
import { Redirect, Route, Switch } from 'react-router';
import { TasksView, NotFoundView } from './containers';

import { createOauthFlow } from 'react-oauth-flow';

//import { Sender, Receiver } from './components/createOauthFlow.js';

const { Sender, Receiver } = createOauthFlow({
    authorizeUrl: 'https://oauth.web.cern.ch/OAuth/Authorize',
    tokenUrl: 'https://oauth.web.cern.ch/OAuth/Token',
    clientId: 'wc-dev.cern.ch',
    clientSecret: 'tGL20KCnoSe3e8quwtjPSR1IpgyGOiF8JsqyAew2F6I1',
    redirectUri: 'https://wc-dev.cern.ch/login',
});

const handleSuccess = (accessToken, { response, state }) => {
    console.log('Success!');
    console.log('AccessToken: ', accessToken);
    console.log('Response: ', response);
    console.log('State: ', state);
};

const handleError = async error => {
    console.error('Error02: ', error.message);
    console.error('errrorrrr:', error);
 };


export default(
    <Switch>
        //<Route exact path="/tasks" component={TasksView} />
        <Route exact path="/" render={
            () => (
                <Sender
                render={({ url }) => <a href={url}>Connect to CERN SSO</a>}
                />
            )
        }/>
        <Route exact path="/login" render={({ location }) => (
            <Receiver

            location={location}
            onAuthSuccess={handleSuccess}
            onAuthError={handleError}
            render={
                ({processing,state,error}) => {
                    if (processing) {
                        return <h1>Processing!</h1>;
                    }
                    if (error) {
			return <p style={{ color: 'red' }}>{error.message}}</p>;
                    }
                    return <Redirect to='/tasks' />;
                }}
                />

        )}
        />
        <Route path="*" component={NotFoundView} />
    </Switch>
);
