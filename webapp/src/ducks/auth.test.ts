import React from 'react';
import { render, screen } from '@testing-library/react';
//import thunk from 'redux-thunk'
//import configureMockStore from 'redux-mock-store'
import auth, { AuthState, LoginAction, LogoutAction} from './auth';
import { UserInfo } from '../common/types';

//const middlewares = [thunk]
//const mockStore = configureMockStore(middlewares)


/** ******************************************* */
/* Test reducer                                 */
/** ******************************************* */

describe('Test auth reducer', (): void => {

    /** ******************************************* */
    /* Variables needed for the tests               */
    /** ******************************************* */
    const dummyUserInfo : UserInfo = {
        user: "Dummy",
        accessToken: "dummyAccessToken",
        refreshToken: "dummyRefreshToken"
    };
    const state : AuthState = {
        user: dummyUserInfo
    }

    it('should test auth reducer after a dummy action', () : void => {
        
        const inputState = state;
        const outputState = state;
        const testDummyAction = {
            type: 'AUTH/DUMMY_ACTION'
        }

        expect(auth(inputState, testDummyAction)).toEqual(outputState);
    });

    it('should test auth reducer after LoginAction', () : void => {
        const inputState = {user : ''};
        const outputState = state;
        const testLoginAction : LoginAction = {
            type: 'AUTH/LOGIN',
            payload: dummyUserInfo
        }

        expect(auth(inputState, testLoginAction)).toEqual(outputState);
    });
    
    it('should test auth reducer after LogoutAction', () : void => {
        const inputState = state;
        const outputState = {};
        const testLogoutAction : LogoutAction = {
            type: 'AUTH/LOGOUT'
        }
        expect(auth(inputState, testLogoutAction)).toEqual(outputState);
    });

})