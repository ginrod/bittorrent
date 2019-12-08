<template>
  <div class="index">
    <h1>{{ msg }}</h1>
    <ul>
        <input v-model="pattern" placeholder="Write a name or pattern">
         <button type="button" class="btn btn-default btn-sm" style="background-color:Green; color:White" v-on:click="search()">
           Search</button>
      </ul>
    <ul>
      <button class="btn btn-default btn-sm" style="background-color:Green; color:White" v-on:click="show_shared_files()"> Go to Shared Files</button>
      <!-- <li><a href="/shared-files">Shared Files</a></li> -->
    </ul>
    <h3>Downloads In Progress</h3>
    <ul></ul>
     <div style="text-align:center;">
      <table align="center" border="0" cellspacing="50">
          <tr>
              <th>File Name</th>
              <th>Progress</th>
          </tr>
          <tr>
              <td>The Lion King</td>
              <td>50 %</td>
              <td> 
                <button  v-if="paused" type="button" class="btn btn-default btn-sm" style="background-color:yellow; color:black" v-on:click="PausePlay()">Pause</button>         
                <button  v-else type="button" class="btn btn-default btn-sm" style="background-color:Green; color:black" v-on:click="PausePlay()">Play</button>         
              </td>
              <td>
                <button type="button" class="btn btn-default btn-sm" style="background-color:red; color:white">Cancel</button>
              </td>
          </tr>
          <tr>
              <td>The Lion King</td>
              <td>90 %</td>
              <td> 
                <button type="button" class="btn btn-default btn-sm" style="background-color:yellow; color:black">Pause</button>         
              </td>
              <td>
                <button type="button" class="btn btn-default btn-sm" style="background-color:red; color:white">Cancel</button>
              </td>
          </tr>
          <tr>
              <td>Cualquier cosa</td>
              <td>99 %</td>
              <td> 
                <button type="button" class="btn btn-default btn-sm" style="background-color:yellow; color:black">Pause</button>         
              </td>
              <td>
                <button type="button" class="btn btn-default btn-sm" style="background-color:red; color:white">Cancel</button>
              </td>
          </tr>
          <tr>
              <td>The Lion King !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!</td>
              <td>27 %</td>
              <td> 
                <button type="button" class="btn btn-default btn-sm" style="background-color:yellow; color:black">Pause</button>         
              </td>
              <td>
                <button type="button" class="btn btn-default btn-sm" style="background-color:red; color:white">Cancel</button>
              </td>
          </tr>
          
      </table>
    <ul></ul>

    </div>
  </div>
</template>



<script>

export default {
  name: 'Index',
  props:
  {
    downloading_list: [],
    downloading_sizes: [],
    pattern: String,
  },
  data() {
    return {
      downloading_current_sizes: [],
      paused: Boolean,
    };
  },
  methods: {
    show_shared_files() {
      this.$router.push('/shared-files/')
    },
    search()
    {
      this.$router.push('/results/' + this.pattern)
    },
    PausePlay()
    {
      this.paused = !this.paused
      // alert('INSIDE FUNCTION')
    },
  },
  mounted() {
    //   fetch("http://192.168.1.104:5001/downloading").then(function (response) {
    //     return response.json();})
    //     .then(function (result) {
    //       this.downloding_list =  result;
    //       alert()   
    // });
    },
    created() {
      // this.$http.get("https://jsonplaceholder.typicode.com/posts/1")
      // .then(res => {
      //   this.post = res.body;
      //   });  
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

/* td, tr
{
  padding:0 15px;
} */

/* td:nth-child(2) {
 border-top: 0;
 border-bottom: 0;
 border-right: 0 
}

td:nth-child(3) {
 border-top: 0;
 border-bottom: 0;
 border-right: 0;
 border-left: 0;
} */

/* table {
  border-collapse: collapse;
}
table td {
  border: 5px solid black; 
}
table tr:first-child td {
  border-top: 0;
}
table tr td:first-child {
  border-left: 0;
}
table tr:last-child td {
  border-bottom: 0;
}
table tr td:last-child {
  border-right: 0;
} */

</style>
