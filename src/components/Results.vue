<template>
  <div class="results">
    <h1>
      Results of the search of {{ msg }}
    </h1>

    <!-- <input type = "radio"
            name = "radSize"
            id = "sizeSmall"
            value = "small"
            checked = "checked" />
    <label for = "sizeSmall">small</label>
    <input type = "radio"
            name = "radSize"
            id = "sizeMed"
            value = "medium" />
    <label for = "sizeMed">medium</label>
    <input type = "radio"
            name = "radSize"
            id = "sizeLarge"
            value = "large" />
    <label for = "sizeLarge">large</label> -->

    <div style="text-align:center;">
      <table align="center" border="1">
          <tr>
              <th>Name</th>
              <th>Size</th>
              <th></th>
          </tr>
          <tr v-for="el in search_result" :key="el.id">
            <td>{{el.name}}</td>
            <td>{{el.size}}</td>
          </tr>  
          
      </table>
    </div>

    <ul></ul>
    <button type="button" class="btn btn-default btn-sm" style="background-color:green; color:white">Download</button>
    <!-- <button style="background-color:white;">Share New File</button> -->

  </div>
</template>

<script>
export default {
  name: 'SharedFiles',
  props: {
    msg: String,
    pattern: String
  },
  data() {
    return {
      search_result: []
    };
  },
  methods:{
    
  },
  created() {
      this.pattern = this.$route.params.pattern;
      this.msg = this.pattern;
      if (this.pattern === undefined) {
        this.pattern = ""
        this.msg = "[All]"
      }
      alert(this.pattern)
      fetch("http://192.168.1.104:5001/search/" + this.pattern).then(function (response) {
        return response.json();})
        .then(function (result) {
          this.search_result =  result;
    });
    },
    mounted() {
      
    },
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>
