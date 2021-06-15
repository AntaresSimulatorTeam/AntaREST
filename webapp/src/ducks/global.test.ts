import React from 'react';
import { render, screen } from '@testing-library/react';
import { v4 as uuidv4 } from 'uuid';
import global,
{ GlobalState,
  AddOnCloseListenerAction,
  RemoveOnCloseListenerAction,
  removeOnCloseListener,
  addOnCloseListener,
} from './global';
import { UserInfo } from '../common/types';

// Mock uuid
jest.mock('uuid');

/** ******************************************* */
/* Test actions                                 */
/** ******************************************* */

describe('Test global actions', (): void => {
  // ADD action
  it('should test add action', (): void => {
    // Mocking uuidv4 function
    const expectedUuid = '75442486-0878-440c-9db1-a7006c25a39f';
    (uuidv4 as jest.Mock).mockReturnValue(expectedUuid); // <= use a type assertion

    // Listener
    const confirmMessage = 'Response is always 42';
    const listener = () => confirmMessage;

    // Mocking dispatch function
    const mockDispatch: jest.Mock<any, any> = jest.fn();

    // Call addOnCloseListener function
    const result: string = addOnCloseListener(listener)(mockDispatch);

    // Dispatch has to be called once
    expect(mockDispatch).toHaveBeenCalledTimes(1);

    // Dispatch has to be called with following action
    expect(mockDispatch).toHaveBeenCalledWith({
      type: 'GLOBAL/ADD_ONCLOSE_LISTENER',
      payload: { id: expectedUuid, listener: expect.any(Function) },
    });

    // function has to return the listener id
    expect(result).toEqual(expectedUuid);
  });

  // REMOVE action
  it('should test remove action', (): void => {
    // Expected action
    const expectedAction: RemoveOnCloseListenerAction = {
      type: 'GLOBAL/REMOVE_ONCLOSE_LISTENER',
      payload: 'id',
    };

    expect(removeOnCloseListener('id')).toEqual(expectedAction);
  });
});

/** ******************************************* */
/* Test reducer                                 */
/** ******************************************* */

describe('Test global reducer', (): void => {
  /** ******************************************* */
  /* Variables needed for the tests               */
  /** ******************************************* */

  // Common state
  const initialState: GlobalState = {
    onCloseListeners: {},
  };

  // Common listener
  const listener = (event: Event) => console.log('Response is always 42');

  it('should test global reducer after a dummy action', (): void => {
    const state: GlobalState = {
      onCloseListeners: { id: (event: Event) => console.log('Listener') },
    };
    const inputState = state;
    const outputState = state;
    const testDummyAction: Action = {
      type: 'GLOBAL/DUMMY_ACTION',
    };

    expect(global(inputState, testDummyAction)).toEqual(outputState);
  });

  it('should test global reducer after adding listener action', (): void => {
    const testAddAction: AddOnCloseListenerAction = {
      type: 'GLOBAL/ADD_ONCLOSE_LISTENER',
      payload: {
        id: 'id',
        listener,
      },
    };
    const inputState: GlobalState = initialState;
    const outputState: GlobalState = {
      onCloseListeners: { [testAddAction.payload.id]: testAddAction.payload.listener },
    };

    expect(global(inputState, testAddAction)).toEqual(outputState);
  });

  it('should test global reducer after removing listener action', (): void => {
    const testRemoveAction: RemoveOnCloseListenerAction = {
      type: 'GLOBAL/REMOVE_ONCLOSE_LISTENER',
      payload: 'id',
    };
    const outputState: GlobalState = initialState;
    const inputState: GlobalState = {
      onCloseListeners: { [testRemoveAction.payload]: listener },
    };

    expect(global(inputState, testRemoveAction)).toEqual(outputState);
  });
});
