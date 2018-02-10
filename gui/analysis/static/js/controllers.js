angular.module('challengerApp.controllers', [])
  .controller('ExperimentController', function ($scope, $stateParams, $uibModal, ExperimentService) {
    $scope.id = $stateParams.id
    $scope.experiment_v2 = ExperimentService.get({ id: $stateParams.id })
    $scope.open_graph = graph_popup_factory($uibModal)
    $scope.open_csv = csv_popup_factory($uibModal)
    $scope.download_csv = csv_download_factory()
  })
  .controller('VariableController', function ($scope, $stateParams, $uibModal, SummaryGraphService) {
    $scope.id = $stateParams.id
    $scope.graphs = SummaryGraphService.get({ variable: $stateParams.id })
    $scope.open_graph = graph_popup_factory($uibModal)
    $scope.open_csv = csv_popup_factory($uibModal)
    $scope.download_csv = csv_download_factory()
  })
  .controller('HomeController', function ($scope, $uibModal, SummaryDataAllService) {
    $scope.data = SummaryDataAllService.get()
    $scope.open_csv = csv_popup_factory($uibModal)
    $scope.download_csv = csv_download_factory()
  })
  .controller('ModalInstanceCtrl', function ($uibModalInstance, data) {
    var $ctrl = this
    $ctrl.data = data
    $ctrl.ok = function () {
      $uibModalInstance.close()
    }
  })
  .controller('MenuController', function ($scope, $state, ExperimentService) {
    ExperimentService.query().$promise.then(function (result) {
      $scope.tree.push({ label: 'Home', children: [], data: '/#/' })
      $scope.tree.push({ label: 'Variables', children: result.variables })
      $scope.tree.push({ label: 'Experiments', children: result.experiments })
    })
    $scope.tree = []
    $scope.tree_handler = function (branch) {
      if (branch.data)
        window.location.href = branch.data
    // $state.go('experiments_view', { id: branch.data.id })
    }
  }).controller('DataController', function ($scope, $state, $stateParams, DataService) {
  $scope.id = $stateParams.id
  $scope.filter_text = ''
  $scope.filtered_data = []
  $scope.on_filter = function () {
    $scope.filtered_data = { 'status': 'Loading....' }
    DataService.query({ id: $stateParams.id, filter: $scope.filter_text }).$promise.then(function (result) {
      $scope.filtered_data = result.items
    })
  }
})

function graph_popup_factory ($uibModal) {
  return function (graph_data) {
    var modalInstance = $uibModal.open({
      animation: true,
      ariaLabelledBy: 'modal-title',
      ariaDescribedBy: 'modal-body',
      templateUrl: '/static/templates/graph_popup_content.html',
      controller: 'ModalInstanceCtrl',
      controllerAs: '$ctrl',
      size: 'lg',
      resolve: {
        data: function () {
          return graph_data
        }
      }
    })
  }
}

function csv_popup_factory ($uibModal) {
  return function (cvs_data) {
    var modalInstance = $uibModal.open({
      animation: true,
      ariaLabelledBy: 'modal-title',
      ariaDescribedBy: 'modal-body',
      templateUrl: '/static/templates/csv_popup_content.html',
      controller: 'ModalInstanceCtrl',
      controllerAs: '$ctrl',
      size: 'lg',
      resolve: {
        data: function () {
          var parsed = cvs_data.split('\n')
          var data = []
          for (var i = 1; i < parsed.length; i++) {
            var line = parsed[i]
            if (!line) continue
            data.push(line.split(','))
          }
          return { headers: parsed[0].split(','), body: data }
        }
      }
    })
  }
}

function csv_download_factory () {
  return function (name, cvs_data) {
    var a = angular.element('<a></a>')
    a.attr('href', 'data:application/octet-stream;base64,' + btoa(cvs_data))
    a.attr('style', 'display:none')
    a.attr('download', name + '.csv')
    a[0].click()
    a.remove()
  }
}
