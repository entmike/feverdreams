import React from 'react';
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BsDice3 } from 'react-icons/bs';
import {
  Button,
  Box,
  HStack,
  Heading,
  Image,
  Skeleton,
  Text,
  SimpleGrid,
  Code,
  Kbd,
  Grid,
  GridItem,
  Textarea,
  IconButton,
  FormControl,
  FormHelperText,
  FormLabel,
  Input,
  NumberDecrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  RadioGroup,
  Radio,
  Stack,
  Switch,
  Select,
  Checkbox,
  VStack,
  Center,
  Wrap,
  WrapItem
} from '@chakra-ui/react';
import { useAuth0 } from '@auth0/auth0-react';
import { join, update } from 'lodash';
import { AddIcon, DeleteIcon } from '@chakra-ui/icons';
import { id } from 'date-fns/locale';

// TODO: This isAuthenticated/token stuff should be in a context <- Agreed, -Mike.
function MutateStablePage({ isAuthenticated, token, mode }) {
  const [job, setJob] = useState(null);
  let sh = localStorage.getItem("show-mutate-help");
  let pr = localStorage.getItem("private-settings");
  let bs = localStorage.getItem("batchsize-settings");
  let showhelp = (sh==='false')?false:true
  let privatesettings = (pr==='true')?true:false
  let batch_size = bs?parseInt(bs):5
  const [batchSize, setBatchSize] = useState(batch_size);
  const [show_help, setShowHelp] = useState(showhelp);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth0();
  const params = useParams();
  const navigate = useNavigate();

  async function getJob(job_uuid) {
    setLoading(true);
    let discord_id
    if(user){
      discord_id = user.sub.split("|")[2]
    }
    try {
      const jobData = await fetch(
        `${process.env.REACT_APP_api_url}/v3/meta/${job_uuid}`,
        {
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
        }
      )
        .then((response) => {
          let data = response.json()
          return data
        })
        .then((data) => {
          if (!data){
            data = {
              uuid : job_uuid,
              views : 0,
              str_author : discord_id,
              gpu_preference : "medium",
              editable : true,
              private : privatesettings,
              nsfw: false,
              review: true,
              params:{
                restore_faces : false,
                enable_hr : false,
                width_height:[ 1024, 512 ],
                seed: -1,
                scale : 7.0,
                eta : 0.0,
                steps: 50,
                prompt: "A beautiful painting of a singular lighthouse, shining its light across a tumultuous sea of blood by greg rutkowski and thomas kinkade, Trending on artstation",
                negative_prompt : "",
                repo : "a1111",
                sampler: "k_euler_ancestral"
              }
            }
          }else{
            data.review = true
            data.private = privatesettings
            data.params.repo = "a1111"
          }

        if(mode==="edit"){
          if(user){
            discord_id = user.sub.split("|")[2]
            if(discord_id !== data.str_author){
              data.editable = false
            }else{
              data.editable = (data.status === "queued" || data.status === "rejected" || data.status === "failed")
            }
          }
        }else{
          data.editable = true
        }
        return data;
      });

      if (jobData) {
        setJob(jobData);
        setLoading(false);
      }
      setLoading(false);
    } catch (error) {
      console.log('Unable to get job...');
    }
  }

  useEffect(() => {
    params && getJob(params.uuid);
  }, [token]);
  
  async function save() {
    try {
      // return
      setLoading(true)
      let j = JSON.parse(JSON.stringify(job))
      j.batch_size = batchSize
      console.log(j)
      const { success: mutateSuccess, results: results } = await fetch(
        `${process.env.REACT_APP_api_url}/v3/create/${mode}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ job: j }),
        }
      )
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        return data;
      });

      if (mutateSuccess) {
        if(mode==="mutate"){
          if(results){
            // console.log(results)
            navigate(`/myworkspace/1`);
          }
        }
        if(mode==="edit"){
          navigate(`/piece/${results[0].uuid}`);
        }
      }
      setLoading(false);
    } catch (error) {
      console.log('Unable to mutate.');
    }
  }

  if (!isAuthenticated) {
    return <Text>You are not logged in. To mutate, log in first.</Text>
  }

  if(job){
      if(!job.params && !loading){
        return <Text>This piece is private.</Text>
      }else{
        return (
          <>
            <Center>
              <Box maxW={"1024px"}>
                <Skeleton isLoaded={!loading}>
                  <Center>
                    <VStack>
                      <Heading size={"sm"}>{mode==="mutate"?"Mutate":"Edit"}</Heading>
                      {/* <Text fontSize='xs' noOfLines={1}>{job ? job.uuid : 'Loading'}</Text> */}
                      {job.uuid && <Image src={`https://images.feverdreams.app/thumbs/512/${job.uuid}.jpg`}></Image>}
                    </VStack>
                  </Center>
                  <SimpleGrid columns={{sm: 1, md: 3}} spacing="20px">
                    <FormControl>
                      <FormLabel htmlFor="show_help">🤔 Show Help</FormLabel>
                      <Switch
                        id="show_help"
                        isChecked = {show_help}
                        onChange={(event) => {
                          localStorage.setItem("show-mutate-help",event.target.checked)
                          setShowHelp(event.target.checked)
                        }}
                      />
                      {show_help && <FormHelperText>Show parameter help</FormHelperText>}
                    </FormControl>
                    <FormControl>
                      <FormLabel htmlFor="private">Private Settings</FormLabel>
                      <Switch isDisabled = {!job.editable}
                        id="private"
                        isChecked={(job.private===true)?true:false}
                        onChange={(event) => {
                          localStorage.setItem("private-settings",event.target.checked)
                          let updatedJob = JSON.parse(JSON.stringify(job));
                          updatedJob.private = event.target.checked ? true : false;
                          setJob({ ...job, ...updatedJob });
                        }}
                      />
                      {show_help && <FormHelperText>Keep settings private</FormHelperText>}
                    </FormControl>
                    {/* <FormControl>
                      <FormLabel htmlFor="review">Review</FormLabel>
                      <Switch isDisabled = {!job.editable}
                        id="review"
                        isChecked={(job.review===true)?true:false}
                        onChange={(event) => {
                          localStorage.setItem("review-settings",event.target.checked)
                          let updatedJob = JSON.parse(JSON.stringify(job));
                          updatedJob.review = event.target.checked ? true : false;
                          setJob({ ...job, ...updatedJob });
                        }}
                      />
                      {show_help && <FormHelperText>Review results before publishing</FormHelperText>}
                    </FormControl> */}
                    {mode!=="edit" && <><FormControl>
                      <FormLabel htmlFor="batch_size">Batch Size</FormLabel>
                      <NumberInput isDisabled = {!job.editable}
                        id="batch_size"
                        value={batchSize}
                        min={1}
                        max={15}
                        clampValueOnBlur={true}
                        onChange={(value) => {
                          let bs = parseInt(value);
                          localStorage.setItem("batchsize-settings",bs)
                          setBatchSize(bs);
                        }}
                      >
                        <NumberInputField />
                        <NumberInputStepper>
                          <NumberIncrementStepper />
                          <NumberDecrementStepper />
                        </NumberInputStepper>
                      </NumberInput>
                      {show_help && <FormHelperText>
                        Number of images to generate.
                      </FormHelperText>}
                    </FormControl>
                    </>}
                    {/* <FormControl>
                      <FormLabel htmlFor="agent_preference">Agent Preference (temporary)</FormLabel>
                      <Input
                        id="agent_preference"
                        value={job.agent_preference?job.agent_preference:"any"}
                        onChange={(event) => {
                          let updatedJob = JSON.parse(JSON.stringify(job));
                          updatedJob.agent_preference = event.currentTarget.value;
                          setJob({ ...job, ...updatedJob });
                        }}
                      />
                      {show_help && <FormHelperText>Agent Preference (temporary) - Allows you to prefer a specific agent by ID for testing/sizing reasons.  Leave as "any" for normal behavior.</FormHelperText>}
                    </FormControl> */}
                  </SimpleGrid>
                  <FormControl>
                    <FormLabel htmlFor="prompt">Prompt</FormLabel>
                      <Textarea
                        isDisabled = {!job.editable}
                        id={`prompt`}
                        type="text"
                        value={job.params.prompt}
                        onChange={(event) => {
                          let prompt = event.target.value
                          // if(!prompt) prompt=" "
                          let updatedJob = JSON.parse(JSON.stringify(job));
                          updatedJob.params.prompt = prompt;
                          setJob({ ...job, ...updatedJob });
                        }}
                      />
                      {show_help && <FormHelperText>Phrase, sentence, or string of words and phrases describing what the image should look like. The words will be analyzed by the AI and will guide the diffusion process toward the image you describe.</FormHelperText>}
                  </FormControl>
                  <FormControl>
                    <FormLabel htmlFor="negative_prompt">Negative Prompt</FormLabel>
                      <Textarea
                        isDisabled = {!job.editable}
                        id={`negative_prompt`}
                        type="text"
                        value={job.params.negative_prompt}
                        onChange={(event) => {
                          let negative_prompt = event.target.value
                          // if(!prompt) prompt=" "
                          let updatedJob = JSON.parse(JSON.stringify(job));
                          updatedJob.params.negative_prompt = negative_prompt;
                          setJob({ ...job, ...updatedJob });
                        }}
                      />
                      {show_help && <FormHelperText>Stuff you want excluded from your image.</FormHelperText>}
                  </FormControl>
                  <Wrap>
                    <WrapItem><FormControl>
                      <FormLabel htmlFor="enable_hr">Highres. Fix</FormLabel>
                      <Switch
                          id="enable_hr"
                          isChecked = {job.params.enable_hr}
                          onChange={(event) => {
                            let enable_hr = event.target.checked
                            let updatedJob = JSON.parse(JSON.stringify(job));
                            updatedJob.params.enable_hr = enable_hr;
                            setJob({ ...job, ...updatedJob });
                          }}
                        />
                    </FormControl>
                    </WrapItem>
                    <WrapItem>
                      <FormControl>
                        <FormLabel htmlFor="restore_faces">Restore Faces</FormLabel>
                        <Switch
                            id="restore_faces"
                            isChecked = {job.params.restore_faces}
                            onChange={(event) => {
                              let restore_faces = event.target.checked
                              let updatedJob = JSON.parse(JSON.stringify(job));
                              updatedJob.params.restore_faces = restore_faces;
                              setJob({ ...job, ...updatedJob });
                            }}
                          />
                      </FormControl>
                    </WrapItem>
                </Wrap>
                  <FormControl>
                    <FormLabel htmlFor="sampler">Sampler</FormLabel>
                    <Select isDisabled = {!job.editable} 
                        id = "sampler"
                        value={job.params.sampler} onChange={(event) => {
                        let updatedJob = JSON.parse(JSON.stringify(job));
                        let value = event.target.selectedOptions[0].value;
                        updatedJob.params.sampler = value
                        setJob({ ...job, ...updatedJob });
                      }}>
                      {
                        [
                          {"key" : "k_lms", "text" : "k_lms"},
                          {"key" : "ddim", "text" : "ddim"},
                          {"key" : "plms", "text" : "plms"},
                          {"key" : "k_euler", "text" : "k_euler"},
                          {"key" : "k_euler_ancestral", "text" : "k_euler_ancestral"},
                          {"key" : "k_heun", "text" : "k_heun"},
                          {"key" : "k_dpm_2", "text" : "k_dpm_2"},
                          {"key" : "k_dpm_2_ancestral", "text" : "k_dpm_2_ancestral"},
                        ].map(shape=>{
                          return <option value={shape.key}>{shape.text}</option>
                        })
                      }
                    </Select>
                    {show_help && <FormHelperText>Sampler</FormHelperText>}
                  </FormControl>
                  <SimpleGrid columns={{sm: 2, md: 4}} spacing="20px">
                    <FormControl>
                      <FormLabel htmlFor="seed">Image Seed</FormLabel>
                      <HStack>
                      <NumberInput isDisabled = {!job.editable}
                        id="seed"
                        value={job.params.seed}
                        min={-1}
                        max={2 ** 32}
                        clampValueOnBlur={true}
                        onChange={(value) => {
                          let updatedJob = JSON.parse(JSON.stringify(job));
                          updatedJob.params.seed = parseInt(value);
                          setJob({ ...job, ...updatedJob });
                        }}
                      >
                        <NumberInputField />
                        <NumberInputStepper>
                          <NumberIncrementStepper />
                          <NumberDecrementStepper />
                        </NumberInputStepper>
                      </NumberInput>
                      <IconButton
                        isRound
                        variant={"ghost"}
                        // colorScheme={'blue'}
                        size="md"
                        onClick={() => {
                          let updatedJob = JSON.parse(JSON.stringify(job))
                          let r = Math.floor(Math.random() * (2**32))
                          updatedJob.params.seed = parseInt(r)
                          setJob({ ...job, ...updatedJob })
                        }}
                        // ml={1}
                        icon={<BsDice3 />}
                      ></IconButton>
                      </HStack>
                      {show_help && <FormHelperText>
                        Image seed used during rendering. Specify -1 for a random seed.
                      </FormHelperText>}
                    </FormControl>
                    <FormControl>
                      <FormLabel htmlFor="steps">Steps</FormLabel>
                      <NumberInput isDisabled = {!job.editable}
                        id="steps"
                        value={job.params.steps}
                        min={10}
                        max={150}
                        clampValueOnBlur={true}
                        onChange={(value) => {
                          let updatedJob = JSON.parse(JSON.stringify(job));
                          updatedJob.params.steps = parseInt(value);
                          setJob({ ...job, ...updatedJob });
                        }}
                      >
                        <NumberInputField />
                        <NumberInputStepper>
                          <NumberIncrementStepper />
                          <NumberDecrementStepper />
                        </NumberInputStepper>
                      </NumberInput>
                      {show_help && <FormHelperText>
                        Increasing steps will provide more opportunities for the AI to
                        adjust the image, and each adjustment will be smaller, and thus will
                        yield a more precise, detailed image. Increasing steps comes at the
                        expense of longer render times.
                      </FormHelperText>}
                    </FormControl>
                    <FormControl>
                      <FormLabel htmlFor="scale">
                        Scale
                      </FormLabel>
                      <NumberInput isDisabled = {!job.editable}
                        id="scale"
                        value={job.params.scale}
                        precision={2}
                        step={0.1}
                        min={1}
                        max={15}
                        onChange={(value) => {
                          let updatedJob = JSON.parse(JSON.stringify(job));
                          updatedJob.params.scale = parseFloat(value);
                          setJob({ ...job, ...updatedJob });
                        }}
                      >
                        <NumberInputField />
                        <NumberInputStepper>
                          <NumberIncrementStepper />
                          <NumberDecrementStepper />
                        </NumberInputStepper>
                      </NumberInput>
                      {show_help && <FormHelperText>
                        Scale, like clip_guidance_scale but not.
                      </FormHelperText>}
                    </FormControl>
                  <FormControl>
                    <FormLabel htmlFor="eta">ETA</FormLabel>
                    <NumberInput isDisabled = {!job.editable}
                      id="eta"
                      step={0.1}
                      precision={2}
                      value={job.params.eta}
                      min={0.0}
                      max={10}
                      onChange={(value) => {
                        let updatedJob = JSON.parse(JSON.stringify(job));
                        updatedJob.params.eta = parseFloat(value);
                        setJob({ ...job, ...updatedJob });
                      }}
                    >
                      <NumberInputField />
                      <NumberInputStepper>
                        <NumberIncrementStepper />
                        <NumberDecrementStepper />
                      </NumberInputStepper>
                    </NumberInput>
                    {show_help && <FormHelperText>
                      eta (greek letter η) shit man hell if i know.
                    </FormHelperText>}
                  </FormControl>
                    </SimpleGrid>
                    {/* <SimpleGrid columns={{sm: 2, md: 2}} spacing="20px">
                      <FormControl>
                        <FormLabel htmlFor="aspect_ratio">Aspect Ratio Presets</FormLabel>
                        <Select id = "aspect_ratio" isDisabled = {!job.editable} value={job.aspect_ratio} placeholder='Select an aspect ratio...' onChange={(event) => {
                            let updatedJob = JSON.parse(JSON.stringify(job));
                            let value = event.target.selectedOptions[0].value;
                            updatedJob.aspect_ratio = value
                            if(value!=="free"){
                              let w = updatedJob.width_height[0]
                              let w_ratio = parseInt(updatedJob.aspect_ratio.split(":")[0])
                              let h_ratio = parseInt(updatedJob.aspect_ratio.split(":")[1])
                              let w_h = [parseInt(w), parseInt(h_ratio/w_ratio * w)]
                              updatedJob.width_height = w_h;
                            }
                            setJob({ ...job, ...updatedJob });
                          }}>
                          {
                            [
                              {"key" : "free", "text" : "Free"},
                              {"key" : "1:1", "text" : "1:1 (Square)"},
                              {"key" : "16:9", "text" : "16:9 (Film/Display)"},
                              {"key" : "4:5", "text" : "4:5 (Portrait)"},
                              {"key" : "4:1", "text" : "4:1 (Pano)"},
                              {"key" : "1:4", "text" : "1:4 (Skyscraper)"},
                              {"key" : "5:3", "text" : "5:3 (Landscape)"}
                            ].map(shape=>{
                              return <option value={shape.key}>{shape.text}</option>
                            })
                          }
                        </Select>
                        {show_help && <FormHelperText>Shape presets to apply to width/height.  Height will be calculated on aspect ratio based on width.</FormHelperText>}
                      </FormControl>
                      <FormControl>
                        <FormLabel htmlFor="lock_ratio">Lock Aspect Ratio</FormLabel>
                        <Switch isDisabled = {!job.editable && job.aspect_ratio==="free"}
                          id="lock_ratio"
                          isChecked={(job.lock_ratio==="yes"||job.lock_ratio===true)?true:false}
                          onChange={(event) => {
                            let updatedJob = JSON.parse(JSON.stringify(job));
                            updatedJob.lock_ratio = event.target.checked ? true : false;
                            setJob({ ...job, ...updatedJob });
                          }}
                        />
                        {show_help && <FormHelperText>Lock width/height to selected aspect ratio.</FormHelperText>}
                      </FormControl>
                    </SimpleGrid>  */}
                    <SimpleGrid columns={{sm: 3, md: 3}} spacing="20px">
                      <FormControl>
                        <FormLabel htmlFor="width">Width</FormLabel>
                        <NumberInput isDisabled = {!job.editable}
                          id="width"
                          step={64}
                          value={job.params.width_height?job.params.width_height[0]:1280}
                          min={128}
                          max={2560}
                          clampValueOnBlur={true}
                          onChange={(value) => {
                            let updatedJob = JSON.parse(JSON.stringify(job));
                            // updatedJob.params.width_height=updatedJob.width_height || [1280,768]
                            updatedJob.params.width_height[0] = parseInt(value);
                            // if(updatedJob.aspect_ratio !== "free" && updatedJob.lock_ratio){
                            //   let w = updatedJob.params.width_height[0]
                            //   let w_ratio = parseInt(updatedJob.aspect_ratio.split(":")[0])
                            //   let h_ratio = parseInt(updatedJob.aspect_ratio.split(":")[1])
                            //   let w_h = [parseInt(w), parseInt(h_ratio/w_ratio * w)]
                            //   updatedJob.params.width_height = w_h;
                            // }
                            setJob({ ...job, ...updatedJob });
                          }}
                        >
                          <NumberInputField />
                          <NumberInputStepper>
                            <NumberIncrementStepper/>
                            <NumberDecrementStepper/>
                          </NumberInputStepper>
                        </NumberInput>
                        {show_help && <FormHelperText>
                          Image width.  Must be a multiple of 64.
                        </FormHelperText>}
                      </FormControl>
                      <FormControl>
                        <FormLabel htmlFor="height">Height</FormLabel>
                        <NumberInput isDisabled = {!job.editable}
                          id="height"
                          step={64}
                          value={job.params.width_height?job.params.width_height[1]:768}
                          min={128}
                          max={2560}
                          clampValueOnBlur={true}
                          onChange={(value) => {
                            let updatedJob = JSON.parse(JSON.stringify(job));
                            // updatedJob.params.width_height=updatedJob.width_height || [1280,768]
                            updatedJob.params.width_height[1] = parseInt(value);
                            // if(updatedJob.aspect_ratio !== "free" && updatedJob.lock_ratio){
                            //   let h = updatedJob.params.width_height[1]
                            //   let w_ratio = parseInt(updatedJob.aspect_ratio.split(":")[0])
                            //   let h_ratio = parseInt(updatedJob.aspect_ratio.split(":")[1])
                            //   let w_h = [parseInt((w_ratio/h_ratio * h)), parseInt(h)]
                            //   updatedJob.params.width_height = w_h;
                            // }
                            setJob({ ...job, ...updatedJob });
                          }}
                        >
                          <NumberInputField />
                          <NumberInputStepper>
                            <NumberIncrementStepper/>
                            <NumberDecrementStepper/>
                          </NumberInputStepper>
                        </NumberInput>
                        {show_help && <FormHelperText>
                          Image height.  Must be a multiple of 64.
                        </FormHelperText>}
                      </FormControl>
                    </SimpleGrid>
                    {/* <FormControl>
                      <FormLabel htmlFor="nsfw">NSFW?</FormLabel>
                      <Switch isDisabled = {!job.editable}
                        id="nsfw"
                        isChecked={(job.nsfw==="yes"||job.nsfw===true)?true:false}
                        onChange={(event) => {
                          let updatedJob = JSON.parse(JSON.stringify(job));
                          updatedJob.nsfw = event.target.checked ? true : false;
                          setJob({ ...job, ...updatedJob });
                        }}
                      />
                      {show_help && <FormHelperText>Flag as NSFW. This does NOT mean may render racist, illegal, or sexually explicit content</FormHelperText>}
                    </FormControl> */}
                  <Button isDisabled = {!job.editable} onClick={save}>{mode==="edit"?"Edit":"Mutate"}</Button>
                </Skeleton>
              </Box>
            </Center>
          </>
        );
      }
    }
  
}

export default MutateStablePage;
