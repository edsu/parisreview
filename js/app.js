(function(){ 

  var width = 1200;
  var height = 950;
  var color = d3.scale.category20();

  var nodes = [];
  var links = [];
  var index = {};

  function addToIndex(r) {
    var uri = r["@id"];
    if (! index[uri]) {
      var id = nodes.push(r) - 1;
      r.id = id;
      r.size = 1;
      index[uri] = r;
    } 
    for (var p in r) {
      if (! index[uri][p] && r[p]) index[uri][p] = r[p];
    }
    return index[uri];
  }

  ParisReview["@graph"].forEach(function(r) {
    r = addToIndex(r);
    if (r.subject) {
      r.type = 'article'
      r.subject.forEach(function(s) {
        s = addToIndex(s);
        s.type = 'subject';
        links.push({source: r.id, target: s.id});
        r.size += 0.3;
        s.size += 0.3;
      });
    }
    if (r.influencedBy) {
      r.influencedBy.forEach(function(a) {
        a = addToIndex(a);
        links.push({source: r.id, target: a.id});
        a.size += 0.3;
      });
    }
  });

  var svg = d3.select("#viz").append("svg")
    .attr("width", width)
    .attr("height", height);

  var force = d3.layout.force()
    .charge(-280)
    .linkDistance(10)
    .gravity(0.7)
    .size([width, height])
    .nodes(nodes)
    .links(links)
    .start();

  var link = svg.selectAll(".link")
      .data(links)
    .enter().append("line")
      .attr("class", "link")
      .style("stroke", "#222")
      .style("stroke-width", 0.3);

  var node = svg.selectAll(".node")
      .data(nodes)
    .enter().append("circle")
      .attr("class", "node")
      .attr("r", function(d) {return 3 + (d.size * 1.3);})
      .attr("stroke-width", 0.1)
      .attr("stroke", "#555")
      .style("fill", function(d) {
        if (d.type == 'subject') {
          return '#55f';
        } else {
          return 'green';
        }
      })
      .on("mouseover", function() {force.stop();})
      .on("mouseout", function() {force.start();})
      .on("click", function(d) {
        window.open(d['@id'], '_blank');
      })
      .call(force.drag);

  node.append("title")
    .text(function(d) {return d["title"];});

  force.on("tick", function() {
    link.attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });

    node.attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });
  });

})();


