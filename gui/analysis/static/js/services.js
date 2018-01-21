angular.module('challengerApp.services', [])
  .factory('MetricService', function ($resource) {
  return $resource('/api/v1/experiments/:id/metrics/:metric', { id: '@id', metric: '@metric' })
}).factory('DataService', function ($resource) {
  return $resource('/api/v1/data/:id', { id: '@id'}, {
    query: {
      method: 'GET', isArray: false
    }
  })
}).factory('ExperimentService', function ($resource) {
  return $resource('/api/v1/experiments/:id', {id: '@id'}, {
    query: {
      method: 'GET', isArray: false
    }
  })
}).factory('ExperimentServiceV2', function ($resource) {
  return $resource('/api/v2/experiments/:id', {id: '@id'}, {
    query: {
      method: 'GET', isArray: false
    }
  })
}).factory('ExperimentCsvService', function ($resource) {
  return $resource('/api/v1/experiments/:id/csv/:csv', {id: '@id', csv: '@csv'}, null)
}).factory('ExperimentStaticService', function ($resource) {
  return $resource('/api/v1/experiments/:id/static/:static', {id: '@id', static: '@static'}, null)
}).factory('SummaryService', function ($resource) {
  return $resource('/api/v1/summary', null, {
    query: {
      method: 'GET', isArray: false
    }
  })
}).factory('SummaryGraphService', function ($resource) {
  return $resource('/api/v1/summary/graphs/:variable', {variable: '@variable'}, null)
}).factory('SummaryCorrelationService', function ($resource) {
  return $resource('/api/v1/summary/correlations/:variable', {variable: '@variable'}, null)
})
