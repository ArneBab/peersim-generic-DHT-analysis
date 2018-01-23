angular.module('challengerApp.services', []).factory('DataService', function ($resource) {
  return $resource('/api/v1/data/:id', { id: '@id' }, {
    query: {
      method: 'GET', isArray: false
    }
  })
}).factory('ExperimentService', function ($resource) {
  return $resource('/api/v1/experiments/:id', { id: '@id' }, {
    query: {
      method: 'GET', isArray: false
    }
  })
}).factory('SummaryGraphService', function ($resource) {
  return $resource('/api/v1/summary/graphs/:variable', { variable: '@variable' }, null)
})
