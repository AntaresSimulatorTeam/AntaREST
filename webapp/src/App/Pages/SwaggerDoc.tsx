import React from 'react';
import SwaggerUI from 'swagger-ui-react';
import 'swagger-ui-react/swagger-ui.css';
import config from '../../services/config';
import FullPageContainer from '../../components/ui/FullPageContainer';

export default () => (
  <FullPageContainer>
    <SwaggerUI url={`${config.baseUrl}${config.restEndpoint}/swagger.json`} />
  </FullPageContainer>
);
