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
}).factory('RoutingChoiceService', function ($resource) {
  return $resource('/api/v1/experiments/:id/metrics/routing-choice', { id: '@id' })
}).factory('ExperimentService', function ($resource, toastr) {
  return $resource('/api/v1/experiments/:id', {id: '@id'}, {
    query: {
      method: 'GET', isArray: false
    }
  })
}).factory('FileService', function ($resource, $state, $stateParams, $rootScope, toastr) {
  return $resource('/api/v1/files', { path: '@path' }, {
    query: {
      method: 'GET', isArray: false
    }
  })
})
