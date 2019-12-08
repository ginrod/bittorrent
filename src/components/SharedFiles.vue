<template>
  <div class="shared-files">
    <h1>
      Shared Files
    </h1>

    <div style="text-align:center;">
      <table align="center" border="1">
          <tr>
              <th>Name</th>
              <th>Size</th>
          </tr>
          <tr v-for="el in downloding_list" :key="el.id">
            <td>{{el.name}}</td>
            <td>{{el.size}}</td>
          </tr>          
      </table>
    </div>

    <ul></ul>
    <input v-model="path" placeholder="Write a path to share">
    <button type="button" class="btn btn-default btn-sm" style="background-color:green; color:white" v-on:click="share()">Share New File</button>
    <!-- <button style="background-color:white;">Share New File</button> -->

  </div>
</template>

<script>
export default {
  name: 'SharedFiles',
  props: {
    msg: String,
    path: String
  },
  data() {
    return{
      downloding_list: [ 
    ],

    };
  },
  methods: {
    share() {
      // const postData = { path: this.path };
      // this.$http.post("posts", postData)
      // .then(res => {
      //   res.body;
      // });
      fetch('http://192.168.1.104:5001/share', {
        method: 'POST',
        body:JSON.stringify( { path: this.path } )
        }).then((res) => res.json());
    },
  },

  mounted() {
      fetch("http://192.168.1.104:5001/shared").then(function (response) {
        return response.json();})
        .then(function (result) {
          this.downloding_list =  result;
    });
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
