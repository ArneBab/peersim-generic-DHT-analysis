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
}).factory('WoprCaptured', function ($resource, $state, $rootScope, toastr, serverConfig, AuthService) {
  return $resource(serverConfig.wopr_url + '/api/v1/user/captured/:uuid', { uuid: '@uuid' }, {
    get: {
      method: 'GET',
      interceptor: getErrorInterceptor(toastr, $state, $rootScope, AuthService)
    },
    query: {
      method: 'GET', isArray: true,
      interceptor: getErrorInterceptor(toastr, $state, $rootScope, AuthService)
    }
  })
}).factory('UserService', function ($resource, serverConfig, toastr) {
  return $resource(serverConfig.wopr_url + '/api/v1/user', {}, {
    get: {
      method: 'GET'
    }
  })
}).factory('FileService', function ($resource, $state, $stateParams, $rootScope, toastr) {
    return $resource('/api/v1/files', { path: '@path' }, {
      query: {
        method: 'GET', isArray: false,
        interceptor: getErrorInterceptor(toastr, $state, $rootScope)
      }
    })
  })

function extractData(data) {
    return angular.fromJson(data).items;
}

function getErrorInterceptor (toastr, $state, $rootScope) {
  return {
    // This is the responseError interceptor
    responseError: function (response) {
      if (response.data.message) {

        var messages = []
        if (typeof response.data.message === 'string') {
          messages.push(response.data.message)
        } else {
          for (var i in response.data.message) {
            messages.push(response.data.message[i])
          }
        }
        messages.forEach(function (entry) {
          toastr.error(entry, 'Error',
            {
              closeButton: true,
              timeOut: 12000,
              extendedTimeOut: 2000,
              newestOnTop: true
            })
        })
      }
    }
  }
}
