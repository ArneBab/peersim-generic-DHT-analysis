angular.module('challengerApp.controllers', [])
  .controller('ExperimentController', function ($scope, $stateParams, $uibModal, ExperimentService, MetricService) {
    $scope.id = $stateParams.id
    $scope.experiment = ExperimentService.get({id: $stateParams.id})
    $scope.graphs = []

    // load the routing choice graph data
    MetricService.get({id: $stateParams.id, metric: 'stats.json'}).$promise.then(function (result) {
      result.options = stacked_graph_options('Routing Choices: Stacked')
      result.type = 'line'
      $scope.graphs.push(result)
    })

    // load the routing choice graph data
    MetricService.get({id: $stateParams.id, metric: 'path_histo.json'}).$promise.then(function (result) {
      result.options = basic_graph_options('Path Lengths (Hops): Histogram')
      result.type = 'bar'
      $scope.graphs.push(result)
    })

    // load the intercept hop graph data
    MetricService.get({id: $stateParams.id, metric: 'intercept.json'}).$promise.then(function (result) {
      result.options = basic_graph_options('Adversary Intercept Hop: Histogram')
      result.type = 'bar'
      $scope.graphs.push(result)
    })

    // load the intercept hop graph data
    MetricService.get({id: $stateParams.id, metric: 'intercept_calculated.json'}).$promise.then(function (result) {
      result.options = basic_graph_options('Adversary Intercept Hop for Calculated: Histogram')
      result.type = 'bar'
      $scope.graphs.push(result)
    })

    // load the anon graph data
    MetricService.get({id: $stateParams.id, metric: 'anon_set.json'}).$promise.then(function (result) {
      result.options = basic_graph_options('Sender Set Size: Histogram')
      result.type = 'bar'
      $scope.graphs.push(result)
    })

    // load the entropy graph data
    MetricService.get({id: $stateParams.id, metric: 'entropy.json'}).$promise.then(function (result) {
      result.options = basic_graph_options('Entropy: Histogram')
      result.type = 'bar'
      $scope.graphs.push(result)
    })

    $scope.open = function (index) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'myModalContent.html',
        controller: 'ModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          graph: function () {
            return $scope.graphs[index]
          }
        }
      })
    }
  }).controller('ModalInstanceCtrl', function ($uibModalInstance, graph) {
  var $ctrl = this
  $ctrl.graph = graph
  $ctrl.ok = function () {
    $uibModalInstance.close()
  }
})
  .controller('MenuController', function ($scope, $state, ExperimentService) {
    // Build the menu tree from the experiment data
    var builder = function (path_list, path_index, search_items, experiment) {
      if (path_index >= path_list.length)
        return
      path = path_list[path_index]
      item = search_items.find(function (i) {
        return i.label === path
      })
      if (!item) {
        item = {label: path, children: []}
        if (path_index === path_list.length - 1) {
          item.data = experiment
        }
        search_items.push(item)
      }
      return builder(path_list, path_index + 1, item.children, experiment)
    }
    ExperimentService.query().$promise.then(function (result) {
      for (var i = 0; i < result.items.length; i++)
        builder(result.items[i].path.split('/'), 0, $scope.tree, result.items[i])
    })
    // end
    $scope.tree = []
    $scope.tree_handler = function (branch) {
      if (branch.data)
        $state.go('experiments_view', { id: branch.data.id })
    }
  }).controller('DataController', function ($scope, $state, $stateParams, DataService) {
  $scope.id = $stateParams.id
  $scope.filter_text = ''
  $scope.filtered_data = []
  $scope.on_filter = function () {
    $scope.filtered_data = {'status': 'Loading....'}
    DataService.query({id: $stateParams.id, filter: $scope.filter_text}).$promise.then(function (result) {
      $scope.filtered_data = result.items
    })
  }
})

function basic_graph_options (title) {
  return {
    title: {
      display: true,
      text: title
    },
    responsive: true
  }
}

function stacked_graph_options (title) {
  return {
    title: {
      display: true,
      text: title
    },
    responsive: true,
    scales: {
      yAxes: [
        {
          stacked: true
        }
      ]
    }
  }
}
