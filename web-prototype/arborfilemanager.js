function error_message(msg) {
    d3.select(document.body)
        .append("h1")
        .style("color", "red")
        .text(msg);
}

function servicePath(){
    var pathArgs = Array.slice(arguments).join("/");
    if (pathArgs.length > 0) {
        pathArgs = "/" + pathArgs;
    }

    return "../tangelo/projmgr" + pathArgs;
}

window.onload = function () {
    "use strict";

    var hl_proj = null,
        hl_type = null,
        hl_dataset = null;

    function refreshProjects(fade){
        var ajax,
            items,
            fresh;

        ajax = d3.json(servicePath("project"));
        ajax.send("GET", function (e, projects) {
            if (e) {
                error_message("Error!");
                console.log(e);
            }

            items = d3.select("#projects")
                .selectAll("div")
                .data(projects, function (d) {
                    return d;
                });

            fresh = items.enter()
                .append("div")
                .classed("item", true)
                .attr("name", function (d) {
                    return d;
                })
                .text(function (d) {
                    return d;
                })
                .on("click", function (d) {
                    // Move the highlight to the selected project.
                    if (hl_proj !== null) {
                        d3.select("#projects")
                            .select("[name=" + hl_proj + "]")
                            .classed("selected", false);
                    }
                    hl_proj = d;
                    d3.select(this)
                        .classed("selected", true);

                    // Refresh the data type list.
                    refreshDatatypes(hl_proj);

                    // Clear the data set list.
                    clearDatasets();
                });
            fresh.append("a")
                .classed("btn", true)
                .classed("btn-mini", true)
                .text("delete")
                .on("click", function () {
                    deleteProject(d3.select(this).attr("name"));
                });

            if (fade) {
                items.exit()
                    .transition()
                    .duration(1000)
                    .style("height", "0px")
                    .style("opacity", 0.0)
                    .remove();
            } else {
                items.exit()
                    .remove();
            }

            if (hl_proj !== null) {
                refreshDatatypes(hl_proj, fade);
            }
        });
    }

    function refreshDatatypes(project, fade) {
        var ajax,
            items;

        ajax = d3.json(servicePath("project", project));
        ajax.send("GET", function (e, datatypes) {
            if (e) {
                error_message("Error!");
                console.log(e);
                return;
            }

            items = d3.select("#datatypes")
                .selectAll("div")
                .data(datatypes, function (d) {
                    return d;
                });

            items.enter()
                .append("div")
                .classed("item", true)
                .attr("name", function (d) {
                    return d;
                })
                .text(function (d) {
                    return d;
                })
                .on("click", function (d) {
                    // Move the highlight to the selected datatype.
                    if (hl_type !== null) {
                        d3.select("#datatypes")
                            .select("[name=" + hl_type + "]")
                            .classed("selected", false);
                    }
                    hl_type = d;
                    d3.select(this)
                        .classed("selected", true);

                    // Refresh the data set list.
                    refreshDatasets(hl_proj, hl_type);
                });

            if (fade) {
                items.exit()
                    .transition()
                    .duration(1000)
                    .style("height", "0px")
                    .style("opacity", 0.0)
                    .remove();
            } else {
                items.exit()
                    .remove();
            }

            if (hl_dataset !== null) {
                refreshDatatypes(hl_proj, hl_dataset, fade);
            }
        });
    }

    function refreshDatasets(project, type, fade) {
        var ajax,
            items;

        ajax = d3.json(servicePath("project", project, type));
        ajax.send("GET", function (e, datasets) {
            if (e) {
                error_message("Error!");
                console.log(e);
                return;
            }

            items = d3.select("#datasets")
                .selectAll("div")
                .data(datasets, function (d) {
                    return d;
                });

            items.enter()
                .append("div")
                .classed("item", true)
                .attr("name", function (d) {
                    return d;
                })
                .text(function (d) {
                    return d;
                })
                .on("click", function (d) {
                    // Move the highlight to the selected dataset.
                    if (hl_dataset !== null) {
                        d3.select("#datasets")
                            .select("[name=" + hl_dataset + "]")
                            .classed("selected", false);
                    }
                    hl_dataset = d;
                    d3.select(this)
                        .classed("selected", true);
                });

            if (fade) {
                items.exit()
                    .transition()
                    .duration(1000)
                    .style("height", "0px")
                    .style("opacity", 0.0)
                    .remove();
            } else {
                items.exit()
                    .remove();
            }
        });
    }

    function clearDatasets() {
        d3.select("#datasets")
            .selectAll("*")
            .remove();

        hl_dataset = null;
    }

    d3.select("#newproject-ok")
        .on("click", function () {
            var name,
                ajax;

            name = encodeURI(d3.select("#newproject-name").property("value"));

            if (name !== "") {
                ajax = d3.xhr(servicePath("project", name));
                ajax.send("PUT", function (err, response) {
                    if (err) {
                        console.log("error: ");
                        console.log(err);
                        return;
                    }

                    refreshProjects(true);
                });
            }
        });

    refreshProjects(false);
};
