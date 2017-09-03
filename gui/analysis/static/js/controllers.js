angular.module('challengerApp.controllers', [])
  .controller('ExperimentController', function () {
    // do nothing

  }).controller('MenuController', function ($scope, $stateParams, toastr, FileService) {
    $scope.files = FileService.query({ path: $stateParams.path })
})
