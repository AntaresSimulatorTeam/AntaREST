import React from 'react';
import SwaggerUI from 'swagger-ui-react';
import 'swagger-ui-react/swagger-ui.css';
import { getConfig } from '../../services/config';
import FullPageContainer from '../../components/ui/FullPageContainer';

export default () => (
  <FullPageContainer>
    <SwaggerUI url={`${getConfig().baseUrl}${getConfig().restEndpoint}/openapi.json`} />
  </FullPageContainer>
);
