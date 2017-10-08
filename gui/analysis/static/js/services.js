angular.module('challengerApp.services', [])
  .factory('ChallengeServer', function ($resource, $state, $rootScope, toastr, AuthService) {
    return $resource('/api/v1/admin/challenge-servers/:uuid', { uuid: '@uuid' }, {
      update: {
        method: 'PUT'
      },
      get: {
        method: 'GET',
        interceptor: getErrorInterceptor(toastr, $state, $rootScope, AuthService)
      },
      save: {
        method: 'POST',
        interceptor: getErrorInterceptor(toastr, $state, $rootScope, AuthService)
      },
      query: {
        method: 'GET', isArray: true,
        interceptor: getErrorInterceptor(toastr, $state, $rootScope, AuthService)
      },
      remove: { method: 'DELETE' },
      delete: { method: 'DELETE' }
    })
  }).factory('WoprCtfs', function ($resource, $state, $rootScope, toastr, serverConfig, AuthService) {
  return $resource(serverConfig.wopr_url + '/api/v1/admin/ctfs', {}, {
    get: {
      method: 'GET',
      interceptor: getErrorInterceptor(toastr, $state, $rootScope, AuthService)
    }
  })
}).factory('MetricService', function ($resource) {
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
}).factory('SummaryService', function ($resource) {
  return $resource('/api/v1/summary', null, {
    query: {
      method: 'GET', isArray: false
    }
  })
})
